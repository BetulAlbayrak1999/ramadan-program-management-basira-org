from sqlalchemy import Column, Integer, Boolean
from app.database import Base


class SiteSettings(Base):
    """Global site settings."""

    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True)
    enable_email_notifications = Column(Boolean, default=True)
