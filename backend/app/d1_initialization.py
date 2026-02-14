"""
Database initialization for D1 (Cloudflare Workers).

This module handles D1-specific database operations:
- Table creation using raw SQL
- Schema migrations
- Default data seeding
"""
from typing import Dict
from app.d1_adapter import get_d1_binding, execute_d1_batch


async def initialize_d1_database() -> Dict:
    """
    Initialize D1 database with tables, migrations, and default data.
    
    Returns:
        dict: Status report of what was done
    """
    report = {
        "success": False,
        "database_type": "d1",
        "tables_created": False,
        "migrations_applied": [],
        "settings_created": False,
        "admin_created": False,
        "errors": []
    }
    
    try:
        db = get_d1_binding()
        if not db:
            report["errors"].append("D1 binding not available")
            return report
        
        # Drop existing tables to ensure clean schema (safe for initial setup)
        drop_tables_sql = [
            "DROP TABLE IF EXISTS daily_cards",
            "DROP TABLE IF EXISTS users",
            "DROP TABLE IF EXISTS halqas",
            "DROP TABLE IF EXISTS site_settings"
        ]
        
        drop_statements = [db.prepare(sql) for sql in drop_tables_sql]
        await db.batch(drop_statements)
        
        # Create tables using raw SQL
        create_tables_sql = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('participant', 'supervisor', 'admin', 'super_admin')),
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended', 'pending', 'rejected', 'withdrawn')),
                phone TEXT,
                member_id INTEGER UNIQUE,
                supervisor_id INTEGER,
                halqa_id INTEGER,
                gender TEXT,
                age INTEGER,
                country TEXT,
                referral_source TEXT,
                rejection_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supervisor_id) REFERENCES users(id),
                FOREIGN KEY (halqa_id) REFERENCES halqas(id)
            )
            """,
            
            # Halqas table
            """
            CREATE TABLE IF NOT EXISTS halqas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                supervisor_id INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supervisor_id) REFERENCES users(id)
            )
            """,
            
            # Daily cards table
            """
            CREATE TABLE IF NOT EXISTS daily_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                user_id INTEGER NOT NULL,
                quran_tilawa INTEGER DEFAULT 0,
                quran_hifdh INTEGER DEFAULT 0,
                quran_revision INTEGER DEFAULT 0,
                hadith INTEGER DEFAULT 0,
                dua_adhkar INTEGER DEFAULT 0,
                salah_jamaat INTEGER DEFAULT 0,
                salah_qiyam INTEGER DEFAULT 0,
                fasting BOOLEAN DEFAULT FALSE,
                charity BOOLEAN DEFAULT FALSE,
                notes TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
            """,
            
            # Site settings table (matches SQLAlchemy model)
            """
            CREATE TABLE IF NOT EXISTS site_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enable_email_notifications BOOLEAN DEFAULT TRUE
            )
            """
        ]
        
        # Execute table creation
        statements = [db.prepare(sql) for sql in create_tables_sql]
        await db.batch(statements)
        report["tables_created"] = True
        
        # Create default settings (single row matching SQLAlchemy model)
        settings_sql = """
            INSERT INTO site_settings (enable_email_notifications)
            VALUES (TRUE)
        """
        
        await db.prepare(settings_sql).run()
        report["settings_created"] = True
        
        # Create super admin - get credentials from environment
        from app.config import settings as app_settings
        from app.utils.password_hash import bcrypt_hash
        
        admin_email = app_settings.SUPER_ADMIN_EMAIL.lower()
        admin_password_hash = bcrypt_hash.hash(app_settings.SUPER_ADMIN_PASSWORD)
        
        # Use parameterized query to avoid SQL injection
        admin_sql = """
            INSERT OR IGNORE INTO users (
                full_name, email, password_hash, role, status, 
                gender, age, country, phone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await db.prepare(admin_sql).bind(
            'Super Admin',
            admin_email,
            admin_password_hash,
            'super_admin',
            'active',
            'male',
            30,
            'Saudi Arabia',
            '+966000000000'
        ).run()
        
        report["admin_created"] = True
        
        report["success"] = True
        
    except Exception as e:
        report["errors"].append(str(e))
        report["success"] = False
    
    return report


async def is_d1_initialized() -> bool:
    """
    Check if D1 database is already initialized.
    
    Returns:
        True if database is initialized, False otherwise
    """
    try:
        db = get_d1_binding()
        if not db:
            return False
        
        from app.config import settings as app_settings
        admin_email = app_settings.SUPER_ADMIN_EMAIL.lower()
        
        # Check if super admin exists
        result = await db.prepare(
            "SELECT id FROM users WHERE email = ? AND role = 'super_admin'"
        ).bind(admin_email).first()
        
        return result is not None
        
    except Exception:
        return False
