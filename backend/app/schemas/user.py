from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.utils.email_validator import validate_email


# --- Request Schemas ---


class UserRegister(BaseModel):
    full_name: str
    gender: str
    age: int
    phone: str
    email: str
    password: str = Field(min_length=6)
    confirm_password: str
    country: str
    referral_source: str = ""
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        return validate_email(v)


class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        return validate_email(v)


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
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        return validate_email(v)


class ResetPassword(BaseModel):
    email: str
    token: str
    new_password: str = Field(min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        return validate_email(v)


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
    
    # Helper to convert datetime/string to ISO format
    def to_iso(dt):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt  # Already a string, return as-is
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()  # datetime object
        return str(dt)  # Fallback
    
    data = {
        "id": user.id,
        "member_id": user.member_id,
        "full_name": user.full_name if hasattr(user, 'full_name') else user.name,
        "gender": user.gender,
        "age": user.age,
        "phone": user.phone,
        "email": user.email,
        "country": user.country,
        "referral_source": user.referral_source,
        "status": user.status,
        "role": user.role,
        "rejection_note": user.rejection_note if hasattr(user, 'rejection_note') else None,
        "halqa_id": user.halqa_id,
        "halqa_name": user.halqa.name if hasattr(user, 'halqa') and user.halqa else None,
        "created_at": to_iso(getattr(user, 'created_at', None)),
        "updated_at": to_iso(getattr(user, 'updated_at', None)),
    }
    
    if hasattr(user, 'supervised_halqa') and user.supervised_halqa:
        data["supervised_halqa_name"] = user.supervised_halqa.name
    
    if hasattr(user, 'halqa') and user.halqa and hasattr(user.halqa, 'supervisor') and user.halqa.supervisor:
        data["supervisor_name"] = user.halqa.supervisor.full_name if hasattr(user.halqa.supervisor, 'full_name') else user.halqa.supervisor.name
        data["supervisor_phone"] = user.halqa.supervisor.phone
    
    return data
