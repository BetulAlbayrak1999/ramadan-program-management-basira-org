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
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                supervisor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supervisor_id) REFERENCES users(id)
            )
            """,
            
            # Daily cards table (matches SQLAlchemy DailyCard model)
            """
            CREATE TABLE IF NOT EXISTS daily_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                user_id INTEGER NOT NULL,
                quran REAL DEFAULT 0,
                tadabbur REAL DEFAULT 0,
                duas REAL DEFAULT 0,
                taraweeh REAL DEFAULT 0,
                tahajjud REAL DEFAULT 0,
                duha REAL DEFAULT 0,
                rawatib REAL DEFAULT 0,
                main_lesson REAL DEFAULT 0,
                enrichment_lesson REAL DEFAULT 0,
                charity_worship REAL DEFAULT 0,
                extra_work REAL DEFAULT 0,
                extra_work_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
            """,
            
            # Site settings table (matches SQLAlchemy model)
            """
            CREATE TABLE IF NOT EXISTS site_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enable_email_notifications INTEGER DEFAULT 1
            )
            """
        ]
        
        # Execute table creation
        statements = [db.prepare(sql) for sql in create_tables_sql]
        await db.batch(statements)
        report["tables_created"] = True
                
        # Create indexes for performance
        create_indexes_sql = [
            # Users
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_halqa_id ON users(halqa_id)",

            # Daily cards
            "CREATE INDEX IF NOT EXISTS idx_daily_cards_user_id ON daily_cards(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_daily_cards_date ON daily_cards(date)",

            # Halqas
            "CREATE INDEX IF NOT EXISTS idx_halqas_supervisor_id ON halqas(supervisor_id)"
        ]

        index_statements = [db.prepare(sql) for sql in create_indexes_sql]
        await db.batch(index_statements)

        # Create default settings (single row matching SQLAlchemy model)
        settings_sql = """
            INSERT INTO site_settings (enable_email_notifications)
            VALUES (1)
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


async def migrate_daily_cards_schema():
    """
    Migrate daily_cards table to the new schema if needed.
    This preserves users/halqas data and only recreates daily_cards.
    """
    try:
        db = get_d1_binding()
        if not db:
            return

        # Check if the table has the new columns
        result = await db.prepare("PRAGMA table_info(daily_cards)").all()
        if hasattr(result, 'to_py'):
            result = result.to_py()

        columns = set()
        if isinstance(result, dict):
            for row in result.get('results', []):
                columns.add(row.get('name', ''))
        elif isinstance(result, list):
            for row in result:
                if isinstance(row, dict):
                    columns.add(row.get('name', ''))

        # If the new columns exist, no migration needed
        if 'quran' in columns and 'tadabbur' in columns:
            return

        print("Migrating daily_cards table to new schema...")

        # Drop old table and create new one
        await db.prepare("DROP TABLE IF EXISTS daily_cards").run()
        await db.prepare("""
            CREATE TABLE IF NOT EXISTS daily_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                user_id INTEGER NOT NULL,
                quran REAL DEFAULT 0,
                tadabbur REAL DEFAULT 0,
                duas REAL DEFAULT 0,
                taraweeh REAL DEFAULT 0,
                tahajjud REAL DEFAULT 0,
                duha REAL DEFAULT 0,
                rawatib REAL DEFAULT 0,
                main_lesson REAL DEFAULT 0,
                enrichment_lesson REAL DEFAULT 0,
                charity_worship REAL DEFAULT 0,
                extra_work REAL DEFAULT 0,
                extra_work_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
        """).run()
        print("daily_cards table migrated successfully")

    except Exception as e:
        print(f"Error migrating daily_cards: {e}")


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

        if result is not None:
            # DB is initialized, but check if daily_cards needs migration
            await migrate_daily_cards_schema()
            return True

        return False

    except Exception:
        return False
