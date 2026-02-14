"""
Unified database configuration with auto-detection.
Supports both PostgreSQL (traditional server) and D1 (Cloudflare Workers).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
import os

# Lazy initialization globals
_engine = None
_SessionLocal = None


def is_cloudflare_workers():
    """
    Detect if running in Cloudflare Workers environment.
    
    Returns:
        True if in Workers, False otherwise
    """
    # Check multiple indicators for Cloudflare Workers
    if os.getenv("CLOUDFLARE_WORKERS"):
        return True
    if os.getenv("CF_PAGES"):
        return True
    # Check if we're running in Pyodide (Cloudflare uses Pyodide for Python)
    try:
        import sys
        if 'pyodide' in sys.modules:
            return True
    except:
        pass
    
    return False


def detect_environment():
    """
    Detect if running in Cloudflare Workers or traditional server.
    
    Returns:
        'cloudflare' if in Workers environment with D1, 'server' otherwise
    """
    # First check if we're definitely in Cloudflare Workers
    if is_cloudflare_workers():
        return "cloudflare"
    
    # Check if D1 binding is available (set by middleware)
    from app.d1_adapter import is_d1_available
    if is_d1_available():
        return "cloudflare"
    
    # Check if DATABASE_URL indicates SQLite (used by D1)
    if settings.DATABASE_URL.startswith("sqlite"):
        return "cloudflare"
    
    return "server"


def get_engine():
    """
    Get or create database engine based on environment.
    
    For Cloudflare Workers: Returns None (use D1 adapter instead)
    For traditional servers: PostgreSQL engine
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    # In Cloudflare Workers, don't create SQLAlchemy engine at all
    # Use D1 adapter instead (via get_db())
    if is_cloudflare_workers():
        return None
    
    # Only create PostgreSQL engine for traditional servers
    database_url = settings.DATABASE_URL
    _engine = create_engine(
        database_url,
        pool_pre_ping=True
    )
    
    return _engine


def get_session_local():
    """
    Get or create SessionLocal factory.
    
    For Cloudflare Workers: Returns None (use D1 adapter instead) 
    For traditional servers: SQLAlchemy SessionLocal factory
    """
    global _SessionLocal
    
    # In Cloudflare Workers, don't create SQLAlchemy sessions
    # Use D1 adapter instead
    if is_cloudflare_workers():
        return None
    
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None
            
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    
    return _SessionLocal


# Lazy proxy classes for backward compatibility
class _EngineProxy:
    """Proxy that lazily initializes engine on first access."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)


class _SessionLocalProxy:
    """Proxy that lazily initializes SessionLocal on first access."""
    def __call__(self, *args, **kwargs):
        return get_session_local()(*args, **kwargs)


# Module-level exports - these are proxies that initialize lazily
engine = _EngineProxy()
SessionLocal = _SessionLocalProxy()


class Base(DeclarativeBase):
    pass


async def get_db():
    """
    FastAPI dependency: yield a DB session per request (ASYNC).
    
    Automatically detects and uses:
    - D1 binding in Cloudflare Workers (via D1Session)
    - SQLAlchemy session for PostgreSQL (traditional servers)
    
    Made async to support Cloudflare Workers (Pyodide doesn't support threading).
    """
    # Check if D1 binding is available (Cloudflare Workers)
    from app.d1_adapter import is_d1_available, get_d1_binding, D1Session
    
    if is_d1_available():
        # Use D1 in Cloudflare Workers
        db_binding = get_d1_binding()
        session = D1Session(db_binding)
        try:
            yield session
        finally:
            session.close()
    else:
        # Use SQLAlchemy for PostgreSQL (still works in async context)
        session_factory = get_session_local()
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
