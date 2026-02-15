from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import all_routers
from app.config import settings

app = FastAPI(
    title=f"{settings.APP_NAME} v{settings.APP_VERSION}",
    version=settings.APP_VERSION
)

# CORS - Allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://basira.info",
        "https://*.basira.info",
        "https://ramadan-platform-frontend.pages.dev",
        "https://*.ramadan-platform-frontend.pages.dev",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint for quick health check
@app.get("/")
async def root():
    """Root endpoint - confirms API is running."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/api/system/health",
        "system_status": "/api/system/status"
    }


# Custom exception handler: map {"detail": ...} to {"error": ...} for frontend compatibility
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": exc.detail},
    )


# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and log them."""
    import traceback
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    traceback_str = ''.join(traceback.format_tb(exc.__traceback__))
    
    # Log the full error for debugging
    print(f"ERROR: {error_detail}")
    print(f"Traceback: {traceback_str}")
    print(f"Request: {request.method} {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_detail,
            "detail": error_detail,
            "type": type(exc).__name__
        },
    )


# Include all routers with /api prefix
for router in all_routers:
    app.include_router(router, prefix="/api")


# NOTE: Startup logic moved to app/initialization.py for Cloudflare Workers compatibility
# Cloudflare has a 1000ms CPU limit at startup, so heavy DB operations are moved to:
# - POST /system/initialize-database endpoint (manual trigger)
# - Scheduled job via Cloudflare Cron
#
# IMPORTANT: Do NOT import database objects at module level for Workers!
# Use lazy imports inside route handlers only.
#
# For non-Cloudflare deployments with PostgreSQL:
# Uncomment the startup code below and restore the imports:
# from app.database import get_engine, Base
#
# # @app.on_event("startup")
# # def on_startup():
# #     engine = get_engine()
# #     Base.metadata.create_all(bind=engine)

#     # Migrate: add member_id column if missing
#     inspector = inspect(engine)
#     columns = [c["name"] for c in inspector.get_columns("users")]
#     if "member_id" not in columns:
#         with engine.begin() as conn:
#             conn.execute(text("ALTER TABLE users ADD COLUMN member_id INTEGER UNIQUE"))

#     # Migrate: add updated_at column to halqas if missing
#     halqa_columns = [c["name"] for c in inspector.get_columns("halqas")]
#     if "updated_at" not in halqa_columns:
#         with engine.begin() as conn:
#             conn.execute(text("ALTER TABLE halqas ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

#     # Migrate: add tadabbur column to daily_cards if missing
#     daily_card_columns = [c["name"] for c in inspector.get_columns("daily_cards")]
#     if "tadabbur" not in daily_card_columns:
#         with engine.begin() as conn:
#             conn.execute(text("ALTER TABLE daily_cards ADD COLUMN tadabbur DOUBLE PRECISION DEFAULT 0"))

#     db = SessionLocal()
#     try:
#         if not db.query(SiteSettings).first():
#             db.add(SiteSettings(enable_email_notifications=True))
#             db.commit()

#         # Backfill member_id for existing users without one
#         users_without = db.query(User).filter(User.member_id.is_(None)).order_by(User.id).all()
#         if users_without:
#             from sqlalchemy import func
#             max_mid = db.query(func.max(User.member_id)).scalar()
#             next_id = (max_mid + 1) if max_mid else 1000
#             for u in users_without:
#                 u.member_id = next_id
#                 next_id += 1
#             db.commit()
#             print(f"Backfilled member_id for {len(users_without)} users")

#         # Auto-create super admin if not exists
#         admin_email = app_settings.SUPER_ADMIN_EMAIL.lower()
#         admin = db.query(User).filter_by(email=admin_email).first()
#         if not admin:
#             admin = User(
#                 full_name="Super Admin",
#                 gender="male",
#                 age=30,
#                 phone="0000000000",
#                 email=admin_email,
#                 country="--",
#                 status="active",
#                 role="super_admin",
#             )
#             admin.set_password(app_settings.SUPER_ADMIN_PASSWORD)
#             db.add(admin)
#             db.commit()
#             print(f"Super admin created: {admin_email}")
#     finally:
#         db.close()


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