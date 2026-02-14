"""
Database configuration for Cloudflare Workers with D1 support.
This file provides an alternative to the PostgreSQL setup for cloud deployment.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
import os


def get_engine():
    """
    Create database engine based on environment.
    For Cloudflare Workers, use D1 binding (SQLite-based).
    For local development, use PostgreSQL or SQLite.
    """
    database_url = settings.DATABASE_URL
    
    # Check if we're running in Cloudflare Workers environment
    if os.getenv("CLOUDFLARE_WORKER"):
        # For D1, we'd use SQLite engine with the D1 binding
        # Note: You'll need to adapt this based on actual D1 SDK
        database_url = "sqlite:///./ramadan.db"
    
    return create_engine(database_url, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
