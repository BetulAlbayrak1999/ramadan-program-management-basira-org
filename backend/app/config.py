from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://localhost/ramadan_db"

    # JWT
    JWT_SECRET_KEY: str = "change-me"
    JWT_ACCESS_TOKEN_EXPIRES: int = 2592000  # 30 days in seconds
    JWT_ALGORITHM: str = "HS256"

    # Mail
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None

    # Super Admin
    SUPER_ADMIN_EMAIL: str = "admin@example.com"
    SUPER_ADMIN_PASSWORD: str = "xxx"
    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
