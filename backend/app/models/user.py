from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt as bcrypt_hash
from app.database import Base


class User(Base):
    """User model for participants, supervisors, and admins."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, unique=True, nullable=True, index=True)
    full_name = Column(String(200), nullable=False)
    gender = Column(String(10), nullable=False)  # male / female
    age = Column(Integer, nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    referral_source = Column(Text, nullable=True)

    # Status & Roles
    status = Column(String(20), default="pending")  # pending, active, rejected, withdrawn
    role = Column(String(20), default="participant")  # participant, supervisor, super_admin
    rejection_note = Column(Text, nullable=True)

    # Halqa (circle) assignment
    halqa_id = Column(Integer, ForeignKey("halqas.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    halqa = relationship("Halqa", back_populates="members", foreign_keys=[halqa_id])
    daily_cards = relationship("DailyCard", back_populates="user", cascade="all, delete-orphan")
    supervised_halqa = relationship(
        "Halqa", back_populates="supervisor", foreign_keys="Halqa.supervisor_id", uselist=False
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt_hash.hash(password)

    def check_password(self, password: str) -> bool:
        return bcrypt_hash.verify(password, self.password_hash)
