from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Halqa(Base):
    """Halqa (circle/group) model for organizing participants."""

    __tablename__ = "halqas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supervisor = relationship(
        "User", back_populates="supervised_halqa", foreign_keys=[supervisor_id]
    )
    members = relationship(
        "User", back_populates="halqa", foreign_keys="User.halqa_id"
    )
