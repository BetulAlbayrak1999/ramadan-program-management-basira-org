"""
Database initialization logic for Ramadan Program Management API.

This module handles:
- Table creation
- Schema migrations
- Default data seeding
- Database type detection (PostgreSQL vs SQLite/D1)

Moved from main.py startup to support Cloudflare Workers CPU limits.
"""
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError
from app.database import get_engine, Base, get_session_local
from app.models import User, SiteSettings
from app.config import settings as app_settings
import os


def detect_database_type() -> str:
    """
    Detect if we're using PostgreSQL, SQLite (D1), or D1 native.
    
    Returns:
        'postgresql', 'sqlite', or 'd1'
    """
    # Check if in Cloudflare Workers with D1
    from app.d1_adapter import is_d1_available
    if is_d1_available():
        return "d1"
    
    from app.database import is_cloudflare_workers
    if is_cloudflare_workers():
        return "d1"
    
    # Traditional server with SQLAlchemy
    engine = get_engine()
    if engine is None:
        return "d1"  # Assume D1 if no engine
        
    dialect = engine.dialect.name
    return dialect


def is_database_initialized() -> bool:
    """
    Check if database is already initialized by looking for super admin.
    
    Returns:
        True if database is initialized, False otherwise
    """
    # Check if in Cloudflare Workers with D1
    from app.d1_adapter import is_d1_available
    if is_d1_available():
        # Use D1 initialization check (async - can't call from here)
        # Return False to let D1 routes handle it
        return False
    
    from app.database import is_cloudflare_workers
    if is_cloudflare_workers():
        return False  # Let D1 routes handle initialization
    
    # Traditional server with SQLAlchemy
    try:
        SessionLocal = get_session_local()
        if SessionLocal is None:
            return False
        db = SessionLocal()
        try:
            admin_email = app_settings.SUPER_ADMIN_EMAIL.lower()
            admin = db.query(User).filter_by(email=admin_email, role="super_admin").first()
            return admin is not None
        finally:
            db.close()
    except Exception:
        # Database might not exist yet or tables not created
        return False


def initialize_database() -> dict:
    """
    Initialize database with tables, migrations, and default data.
    
    This function is idempotent - safe to call multiple times.
    
    Returns:
        dict: Status report of what was done
    """
    report = {
        "success": False,
        "database_type": detect_database_type(),
        "tables_created": False,
        "migrations_applied": [],
        "settings_created": False,
        "admin_created": False,
        "users_backfilled": 0,
        "errors": []
    }
    
    db_type = report["database_type"]
    engine = get_engine()
    SessionLocal = get_session_local()
    
    try:
        # Step 1: Create all tables
        Base.metadata.create_all(bind=engine)
        report["tables_created"] = True
        
        # Step 2: Apply migrations with DB-specific syntax
        inspector = inspect(engine)
        
        # Migration 1: Add member_id column if missing
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "member_id" not in columns:
            with engine.begin() as conn:
                if db_type == "postgresql":
                    conn.execute(text("ALTER TABLE users ADD COLUMN member_id INTEGER UNIQUE"))
                else:  # SQLite (D1)
                    # SQLite doesn't support ADD COLUMN with constraints in one statement
                    conn.execute(text("ALTER TABLE users ADD COLUMN member_id INTEGER"))
                    # Note: UNIQUE constraint will be enforced at application level for SQLite
            report["migrations_applied"].append("add_member_id_to_users")
        
        # Migration 2: Add updated_at column to halqas if missing
        halqa_columns = [c["name"] for c in inspector.get_columns("halqas")]
        if "updated_at" not in halqa_columns:
            with engine.begin() as conn:
                if db_type == "postgresql":
                    conn.execute(text("ALTER TABLE halqas ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                else:  # SQLite (D1)
                    conn.execute(text("ALTER TABLE halqas ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            report["migrations_applied"].append("add_updated_at_to_halqas")
        
        # Migration 3: Add tadabbur column to daily_cards if missing
        daily_card_columns = [c["name"] for c in inspector.get_columns("daily_cards")]
        if "tadabbur" not in daily_card_columns:
            with engine.begin() as conn:
                if db_type == "postgresql":
                    conn.execute(text("ALTER TABLE daily_cards ADD COLUMN tadabbur DOUBLE PRECISION DEFAULT 0"))
                else:  # SQLite (D1)
                    conn.execute(text("ALTER TABLE daily_cards ADD COLUMN tadabbur REAL DEFAULT 0"))
            report["migrations_applied"].append("add_tadabbur_to_daily_cards")
        
        # Step 3: Create default settings if not exists
        db = SessionLocal()
        try:
            if not db.query(SiteSettings).first():
                db.add(SiteSettings(enable_email_notifications=True))
                db.commit()
                report["settings_created"] = True
            
            # Step 4: Backfill member_id for existing users without one
            users_without = db.query(User).filter(User.member_id.is_(None)).order_by(User.id).all()
            if users_without:
                from sqlalchemy import func
                max_mid = db.query(func.max(User.member_id)).scalar()
                next_id = (max_mid + 1) if max_mid else 1000
                for u in users_without:
                    u.member_id = next_id
                    next_id += 1
                db.commit()
                report["users_backfilled"] = len(users_without)
            
            # Step 5: Auto-create super admin if not exists
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
                report["admin_created"] = True
                
        finally:
            db.close()
        
        report["success"] = True
        
    except Exception as e:
        report["errors"].append(str(e))
        report["success"] = False
    
    return report
