"""
System administration endpoints for database initialization and health checks.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.dependencies import RoleChecker, get_current_user
from app.initialization import initialize_database, is_database_initialized, detect_database_type
from app.config import settings
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/system", tags=["System"])

# Optional security for init endpoint (allows proceeding without auth if token is valid)
optional_security = HTTPBearer(auto_error=False)


@router.get("/debug-db")
async def debug_db(db: Session = Depends(get_db)):
    """Debug endpoint to test database connection."""
    try:
        print("DEBUG: Starting database test...")
        
        from app.models.user import User
        from app.database import is_cloudflare_workers
        from app.d1_adapter import is_d1_available
        
        print(f"DEBUG: is_cloudflare_workers() = {is_cloudflare_workers()}")
        print(f"DEBUG: is_d1_available() = {is_d1_available()}")
        print(f"DEBUG: db type = {type(db)}")
        
        # Try to query users table
        print("DEBUG: Attempting to query users table...")
        users = await db.query(User).all()
        
        print(f"DEBUG: Query successful, found {len(users)} users")
        
        return {
            "success": True,
            "cloudflare_workers": is_cloudflare_workers(),
            "d1_available": is_d1_available(),
            "db_type": str(type(db)),
            "user_count": len(users),
            "users": [{"id": u.id, "email": u.email, "role": u.role} for u in users]
        }
        
    except Exception as e:
        print(f"ERROR in debug_db: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.post("/initialize-database")
async def initialize_database_endpoint(
    x_init_secret: Optional[str] = Header(None, alias="X-Init-Secret"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
):
    """
    Initialize database with tables, migrations, and default data.
    
    Security:
    - Requires super admin authentication (Bearer token)
    - OR valid INIT_SECRET token in X-Init-Secret header
    - Checks if already initialized to prevent duplicate runs
    
    This endpoint:
    1. Creates all database tables
    2. Applies pending migrations
    3. Creates default settings
    4. Creates super admin user
    5. Backfills missing data
    
    Returns detailed report of what was done.
    """
    # Check INIT_SECRET token first (allows init before any users exist)
    # In Cloudflare Workers, secrets are in env vars, not in pydantic settings
    import os
    init_secret = os.getenv('INIT_SECRET') or getattr(settings, 'INIT_SECRET', None)
    has_valid_token = init_secret and x_init_secret == init_secret
    
    # Debug logging (remove after testing)
    print(f"DEBUG: init_secret from env: {os.getenv('INIT_SECRET')}")
    print(f"DEBUG: x_init_secret header: {x_init_secret}")
    print(f"DEBUG: has_valid_token: {has_valid_token}")
    
    # If valid INIT_SECRET provided, skip authentication check
    if not has_valid_token:
        # No valid init secret, so check for super admin authentication
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Requires super admin authentication or valid X-Init-Secret header"
            )
        
        # Manually check authentication (can't use dependency since DB might not be initialized)
        try:
            from app.database import get_db
            from app.utils.jwt_hs256 import jwt, JWTError
            
            # Decode token
            token = credentials.credentials
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check user role
            from app.d1_adapter import is_d1_available, get_d1_binding, D1Session
            from app.models.user import User

            if is_d1_available():
                db = D1Session(get_d1_binding())
            else:
                from app.database import get_session_local
                db = get_session_local()()

            try:
                user = await db.get(User, int(user_id))

                if not user or user.role != "super_admin":
                    raise HTTPException(
                        status_code=403,
                        detail="Requires super admin role"
                    )
            finally:
                db.close()
                
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        except Exception as e:
            # Database might not be initialized yet, only proceed with valid INIT_SECRET
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: {str(e)}. Use X-Init-Secret header for initial setup."
            )
    # If we reach here, either has_valid_token=True OR credentials were validated
    
    # Determine which database system we're using
    # In Cloudflare Workers, always use D1 initialization
    from app.database import is_cloudflare_workers
    
    if is_cloudflare_workers():
        # Use D1 initialization (async)
        from app.d1_initialization import is_d1_initialized, initialize_d1_database
        from app.d1_adapter import is_d1_available
        
        if not is_d1_available():
            raise HTTPException(
                status_code=500,
                detail="D1 binding not available. Ensure D1 database is configured in wrangler.toml"
            )
        
        if await is_d1_initialized():
            return {
                "success": True,
                "message": "D1 database is already initialized",
                "already_initialized": True,
                "database_type": "d1"
            }
        
        # Run D1 initialization
        print("Starting D1 database initialization...")
        report = await initialize_d1_database()
    else:
        # Use PostgreSQL initialization (sync)
        if is_database_initialized():
            return {
                "success": True,
                "message": "Database is already initialized",
                "already_initialized": True,
                "database_type": detect_database_type()
            }
        
        # Run PostgreSQL initialization
        report = initialize_database()
    
    if not report["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {', '.join(report['errors'])}"
        )
    
    return {
        "success": True,
        "message": "Database initialized successfully",
        "report": report
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
    - Database type
    - Initialization status
    - Connection status
    """
    try:
        from app.database import is_cloudflare_workers
        
        if is_cloudflare_workers():
            # D1 database
            from app.d1_initialization import is_d1_initialized
            from app.d1_adapter import is_d1_available
            db_type = "d1"
            initialized = await is_d1_initialized() if is_d1_available() else False
        else:
            # PostgreSQL database
            db_type = detect_database_type()
            initialized = is_database_initialized()
        
        return {
            "status": "healthy",
            "database_type": db_type,
            "database_initialized": initialized
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_initialized": False
        }


@router.get("/status")
async def system_status():
    """
    Basic system status (public endpoint).
    
    Returns:
    - Database type
    - Initialization status
    - Environment info
    
    Note: Detailed metrics require super admin access (use /admin/metrics instead).
    """
    try:
        from app.database import is_cloudflare_workers
        
        if is_cloudflare_workers():
            # D1 database
            from app.d1_initialization import is_d1_initialized
            from app.d1_adapter import is_d1_available
            db_type = "d1"
            initialized = await is_d1_initialized() if is_d1_available() else False
            env_type = "cloudflare"
        else:
            # PostgreSQL database
            db_type = detect_database_type()
            initialized = is_database_initialized()
            env_type = "server"
        
        return {
            "status": "online",
            "database_type": db_type,
            "database_initialized": initialized,
            "environment": env_type
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_initialized": False
        }


@router.get("/check-halqas")
async def check_halqas_raw(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check halqas directly from database (raw SQL)."""
    if current_user.role != "super_admin":
        raise HTTPException(403, detail="Requires super admin role")

    try:
        # Execute raw SQL to see what's actually in the database
        from app.d1_adapter import D1Session

        if isinstance(db, D1Session):
            # D1 database - use direct query
            result = await db.db.prepare("SELECT id, name, supervisor_id, created_at, updated_at FROM halqas").all()
            # D1 returns results in a specific format
            from app.d1_adapter import _convert_js_to_py
            raw_results = _convert_js_to_py(result)
            halqas_raw = raw_results if isinstance(raw_results, list) else raw_results.get('results', [])
        else:
            # PostgreSQL - use SQLAlchemy
            from sqlalchemy import text
            result = await db.execute(text("SELECT id, name, supervisor_id, created_at, updated_at FROM halqas"))
            halqas_raw = [dict(row) for row in result]

        return {
            "message": "Raw database query results",
            "halqas": halqas_raw,
            "count": len(halqas_raw) if isinstance(halqas_raw, list) else 0
        }

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in check_halqas_raw: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(500, detail=error_detail)


@router.post("/fix-halqa-names")
async def fix_halqa_names(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fix any halqas with null or empty names."""
    # Check if user is super admin
    if current_user.role != "super_admin":
        raise HTTPException(403, detail="Requires super admin role")

    try:
        from app.models.halqa import Halqa

        # Query all halqas
        halqas = await db.query(Halqa).all()

        fixed_count = 0
        for halqa in halqas:
            # Check if name is None or empty
            if not halqa.name or halqa.name.strip() == "":
                # Set a default name
                halqa.name = f"حلقة {halqa.id}"
                db.merge(halqa)
                fixed_count += 1

        if fixed_count > 0:
            await db.commit()

        return {
            "message": f"Fixed {fixed_count} halqa(s) with null/empty names",
            "fixed_count": fixed_count
        }

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in fix_halqa_names: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(500, detail=error_detail)
