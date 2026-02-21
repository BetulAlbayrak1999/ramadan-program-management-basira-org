import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings as app_settings
from app.models.user import User
from app.models.site_settings import SiteSettings
from app.dependencies import get_current_user, create_access_token
from app.schemas.user import (
    UserRegister, UserLogin, UserProfileUpdate,
    ChangePassword, ForgotPassword, ResetPassword, user_to_response,
)
from sqlalchemy import func
from app.utils.email import send_new_registration_email, send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory store for reset tokens (use Redis in production)
reset_tokens = {}


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new participant."""
    if data.password != data.confirm_password:
        raise HTTPException(400, detail="كلمتا المرور غير متطابقتين")

    existing = db.query(User).filter_by(email=data.email.lower().strip()).first()
    if existing:
        raise HTTPException(400, detail="البريد الإلكتروني مسجل مسبقاً")

    max_mid = db.query(func.max(User.member_id)).scalar()
    next_member_id = (max_mid + 1) if max_mid else 1000

    user = User(
        member_id=next_member_id,
        full_name=data.full_name.strip(),
        gender=data.gender,
        age=data.age,
        phone=data.phone.strip(),
        email=data.email.lower().strip(),
        country=data.country.strip(),
        referral_source=data.referral_source.strip() if data.referral_source else "",
        status="pending",
        role="participant",
    )
    user.set_password(data.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send notification email
    try:
        site = db.query(SiteSettings).first()
        if site and site.enable_email_notifications:
            send_new_registration_email(user_to_response(user))
    except Exception:
        pass

    return {"message": "تم إرسال طلب التسجيل بنجاح. يرجى انتظار الموافقة."}


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    email = data.email.lower().strip()
    user = db.query(User).filter_by(email=email).first()

    if not user or not user.check_password(data.password):
        raise HTTPException(401, detail="بيانات الدخول غير صحيحة")

    # Check if user is primary super admin - auto-promote before status checks
    is_primary_admin = email == app_settings.SUPER_ADMIN_EMAIL.lower()
    if is_primary_admin and (user.role != "super_admin" or user.status != "active"):
        user.role = "super_admin"
        user.status = "active"
        db.commit()

    if user.status == "pending":
        raise HTTPException(403, detail="طلبك قيد المراجعة. يرجى انتظار الموافقة.")

    if user.status == "rejected":
        note = user.rejection_note or ""
        raise HTTPException(403, detail=f"تم رفض طلبك. {note}")

    if user.status == "withdrawn":
        raise HTTPException(403, detail="حسابك منسحب. تواصل مع الإدارة.")

    token = create_access_token(user.id)
    return {"token": token, "user": user_to_response(user)}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {"user": user_to_response(user)}


@router.put("/profile")
def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    allowed_fields = ["full_name", "phone", "country", "age"]
    for field in allowed_fields:
        value = getattr(data, field, None)
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return {"message": "تم تحديث الملف الشخصي", "user": user_to_response(user)}


@router.post("/change-password")
def change_password(
    data: ChangePassword,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password from within account."""
    if not user.check_password(data.current_password):
        raise HTTPException(400, detail="كلمة المرور الحالية غير صحيحة")

    if data.new_password != data.confirm_password:
        raise HTTPException(400, detail="كلمتا المرور غير متطابقتين")

    user.set_password(data.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """Request password reset."""
    email = data.email.lower().strip()
    user = db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(404, detail="هذا البريد الإلكتروني غير مسجل في النظام")

    token = "".join(random.choices(string.digits, k=6))
    reset_tokens[email] = token
    try:
        send_password_reset_email(email, token)
    except Exception:
        pass

    return {"message": "تم إرسال رمز إعادة التعيين إلى بريدك الإلكتروني"}


@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Reset password with token."""
    email = data.email.lower().strip()

    if reset_tokens.get(email) != data.token:
        raise HTTPException(400, detail="رمز إعادة التعيين غير صحيح")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.set_password(data.new_password)
    db.commit()
    del reset_tokens[email]

    return {"message": "تم إعادة تعيين كلمة المرور بنجاح"}
