from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# --- Request Schemas ---


class UserRegister(BaseModel):
    full_name: str
    gender: str
    age: int
    phone: str
    email: EmailStr
    password: str = Field(min_length=6)
    confirm_password: str
    country: str
    referral_source: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    age: Optional[int] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    confirm_password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(min_length=6)


class AdminResetPassword(BaseModel):
    new_password: str = Field(min_length=6)


class SetRole(BaseModel):
    role: str  # participant, supervisor, super_admin


class AssignHalqa(BaseModel):
    halqa_id: Optional[int] = None


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    referral_source: Optional[str] = None
    status: Optional[str] = None
    halqa_id: Optional[int] = None


class RejectRegistration(BaseModel):
    note: str = ""


# --- Response Helpers ---


def user_to_response(user) -> dict:
    """Build user response dict matching the frontend expected format."""
    data = {
        "id": user.id,
        "member_id": user.member_id,
        "full_name": user.full_name,
        "gender": user.gender,
        "age": user.age,
        "phone": user.phone,
        "email": user.email,
        "country": user.country,
        "referral_source": user.referral_source,
        "status": user.status,
        "role": user.role,
        "rejection_note": user.rejection_note,
        "halqa_id": user.halqa_id,
        "halqa_name": user.halqa.name if user.halqa else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
    if user.supervised_halqa:
        data["supervised_halqa_name"] = user.supervised_halqa.name
    if user.halqa and user.halqa.supervisor:
        data["supervisor_name"] = user.halqa.supervisor.full_name
        data["supervisor_phone"] = user.halqa.supervisor.phone
    return data
