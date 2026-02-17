from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import text, inspect
from app.database import engine, Base, SessionLocal
from app.routes import all_routers
from app.models import User, DailyCard, Halqa, SiteSettings  
from app.config import settings as app_settings
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ramadan Program Management API",
    # Disable docs in production for security
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.middleware("http")
async def log_error_responses(request: Request, call_next):
    response = await call_next(request)
    if response.status_code >= 400:
        client_host = request.client.host if request.client else "-"
        query = f"?{request.url.query}" if request.url.query else ""
        user_agent = request.headers.get("user-agent", "-")
        logger.warning(
            "HTTP %s %s%s -> %s (client=%s ua=%s)",
            request.method,
            request.url.path,
            query,
            response.status_code,
            client_host,
            user_agent,
        )
    return response

# CORS - Restricted to your domain
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Production domain
    "https://basira.info",
    "https://www.basira.info",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted Host Middleware (prevents host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "basira.info", "*.basira.info"]
)


# Custom exception handler: map {"detail": ...} to {"error": ...} for frontend compatibility
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": exc.detail},
    )


# Log and return validation errors (422) with details
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "detail": exc.errors()},
    )


# Include all routers
for router in all_routers:
    app.include_router(router)


# Startup: create tables and default settings
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    # Migrate: add member_id column if missing
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "member_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN member_id INTEGER UNIQUE"))

    # Migrate: add updated_at column to halqas if missing
    halqa_columns = [c["name"] for c in inspector.get_columns("halqas")]
    if "updated_at" not in halqa_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE halqas ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

    # Migrate: add tadabbur column to daily_cards if missing
    daily_card_columns = [c["name"] for c in inspector.get_columns("daily_cards")]
    if "tadabbur" not in daily_card_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE daily_cards ADD COLUMN tadabbur DOUBLE PRECISION DEFAULT 0"))

    db = SessionLocal()
    try:
        if not db.query(SiteSettings).first():
            db.add(SiteSettings(enable_email_notifications=True))
            db.commit()

        # Backfill member_id for existing users without one
        users_without = db.query(User).filter(User.member_id.is_(None)).order_by(User.id).all()
        if users_without:
            from sqlalchemy import func
            max_mid = db.query(func.max(User.member_id)).scalar()
            next_id = (max_mid + 1) if max_mid else 1000
            for u in users_without:
                u.member_id = next_id
                next_id += 1
            db.commit()
            print(f"Backfilled member_id for {len(users_without)} users")

        # Auto-create super admin if not exists
        admin_email = app_settings.SUPER_ADMIN_EMAIL.lower()
        admin = db.query(User).filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                full_name="Super Admin",
                gender="male",
                age=30,
                phone="0000000000",
                email=admin_email,
                country="--",
                status="active",
                role="super_admin",
            )
            admin.set_password(app_settings.SUPER_ADMIN_PASSWORD)
            db.add(admin)
            db.commit()
            print(f"Super admin created: {admin_email}")
    finally:
        db.close()


# Mount static files for frontend (React build output)
frontend_build = Path(__file__).parent / "frontend" / "build"
if frontend_build.exists():
    logger.info(f"✅ Mounting frontend from {frontend_build}")
    
    # Mount static directory for JS/CSS files
    app.mount("/static", StaticFiles(directory=frontend_build / "static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend application (must be LAST route!)"""
        # Block common bot/scanner paths with 404 (don't waste resources serving index.html)
        bot_paths = [
            "wp-", "wordpress", "wp/", "blog/", "phpmyadmin", "admin/",
            "xmlrpc", "wp-content", "wp-includes", ".php", ".asp", ".aspx",
            ".env", ".git", "config", ".xml",  "sitemap", "feed/", "trackback",
            "wlwmanifest.xml", "license.txt", "readme.html"
        ]
        
        if any(pattern in full_path.lower() for pattern in bot_paths):
            logger.warning(f"🚫 Blocked bot/scanner path: {full_path}")
            raise HTTPException(status_code=404, detail="Not found")
        
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Serve root
        if full_path == "" or full_path == "/":
            index_file = frontend_build / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
        
        # Try to serve the file if it exists
        file_path = frontend_build / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # SPA fallback - only serve index.html for legitimate frontend routes
        # Valid frontend routes typically don't have file extensions
        if "." not in full_path:
            index_file = frontend_build / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
        
        # Everything else gets 404
        raise HTTPException(status_code=404, detail="Not found")
else:
    logger.warning(f"⚠️  Frontend build folder not found at {frontend_build}. Frontend will not be served.")
    logger.info("To build the frontend, run: cd frontend && npm install && npm run build")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        reload_excludes=[
            "*/.git/*",
            "*/__pycache__/*",
            "*.pyc",
            "*/.pytest_cache/*",
            "*/.vscode/*",
            "*/.idea/*"
        ],
        reload_delay=1,
        reload_includes=["*.py", "*.html", "*.css", "*.js"]
    )