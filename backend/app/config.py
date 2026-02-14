from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Ramadan Program Management API"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # Database
    # For Cloudflare Workers: D1 binding (env.DB) is used via d1_adapter.py
    # For traditional servers: PostgreSQL connection string
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/ramadan_db")

    # JWT - All from environment for Cloudflare Workers compatibility
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "2592000"))  # 30 days
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Mail - All from environment
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS: bool = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME: str | None = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str | None = os.getenv("MAIL_PASSWORD")

    # Super Admin - From environment
    SUPER_ADMIN_EMAIL: str = os.getenv("SUPER_ADMIN_EMAIL", "admin@example.com")
    SUPER_ADMIN_PASSWORD: str = os.getenv("SUPER_ADMIN_PASSWORD", "change-me-in-production")
    
    # Database Initialization Security
    INIT_SECRET: str | None = os.getenv("INIT_SECRET")
    
    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() in ("true", "1", "yes")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
