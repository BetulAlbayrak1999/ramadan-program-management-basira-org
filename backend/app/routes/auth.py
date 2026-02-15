import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings as app_settings
from app.models.user import User
from app.models.site_settings import SiteSettings
from app.models.halqa import Halqa
from app.dependencies import get_current_user, create_access_token
from app.schemas.user import (
    UserRegister, UserLogin, UserProfileUpdate,
    ChangePassword, ForgotPassword, ResetPassword, user_to_response,
)
from sqlalchemy import func
from app.utils.email import send_new_registration_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory store for reset tokens (use Redis in production)
reset_tokens = {}


@router.post("/register")
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new participant."""
    if data.password != data.confirm_password:
        raise HTTPException(400, detail="كلمتا المرور غير متطابقتين")

    existing = await db.query(User).filter_by(email=data.email.lower().strip()).first()
    if existing:
        raise HTTPException(400, detail="البريد الإلكتروني مسجل مسبقاً")

    last_user = await db.query(User).order_by(User.member_id.desc()).first()
    max_mid = last_user.member_id if last_user else None
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
    await db.commit()
    await db.refresh(user)

    # Send notification email
    try:
        site = await db.query(SiteSettings).first()
        if site and site.enable_email_notifications:
            send_new_registration_email(user_to_response(user))
    except Exception:
        pass

    return {"message": "تم إرسال طلب التسجيل بنجاح. يرجى انتظار الموافقة."}


@router.post("/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    try:
        print(f"Login attempt for: {data.email}")
        
        email = data.email.lower().strip()
        print(f"Querying user with email: {email}")
        
        user = await db.query(User).filter_by(email=email).first()
        
        print(f"User found: {user is not None}")
        
        if not user:
            raise HTTPException(401, detail="بيانات الدخول غير صحيحة")
        
        print(f"Checking password...")
        if not user.check_password(data.password):
            raise HTTPException(401, detail="بيانات الدخول غير صحيحة")
        
        print(f"Password correct, checking admin status...")

        # Check if user is primary super admin - auto-promote before status checks
        is_primary_admin = email == app_settings.SUPER_ADMIN_EMAIL.lower()
        if is_primary_admin and (user.role != "super_admin" or user.status != "active"):
            print(f"Promoting user to super_admin and activating...")
            user.role = "super_admin"
            user.status = "active"
            db.merge(user)  # Mark for update
            await db.commit()
        
        print(f"User status: {user.status}")

        if user.status == "pending":
            raise HTTPException(403, detail="طلبك قيد المراجعة. يرجى انتظار الموافقة.")

        if user.status == "rejected":
            note = user.rejection_note or ""
            raise HTTPException(403, detail=f"تم رفض طلبك. {note}")

        if user.status == "withdrawn":
            raise HTTPException(403, detail="حسابك منسحب. تواصل مع الإدارة.")

        print(f"Creating access token for user {user.id}")
        token = create_access_token(user.id)

        # Load halqa for response
        if user.halqa_id:
            user.halqa = await db.get(Halqa, user.halqa_id)
            if user.halqa:
                if user.halqa.supervisor_id:
                    user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)
                else:
                    user.halqa.supervisor = None

        print(f"Login successful for user {user.id}")
        return {"token": token, "user": user_to_response(user)}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in login: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise HTTPException(500, detail=f"Login failed: {str(e)}")


@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile. Returns a refreshed token to extend the session."""
    # Load halqa for response
    if user.halqa_id:
        user.halqa = await db.get(Halqa, user.halqa_id)
        if user.halqa:
            if user.halqa.supervisor_id:
                user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)
            else:
                user.halqa.supervisor = None

    new_token = create_access_token(user.id)
    return {"user": user_to_response(user), "token": new_token}


@router.put("/profile")
async def update_profile(
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

    db.merge(user)  # Mark for update
    await db.commit()
    await db.refresh(user)

    # Load halqa for response
    if user.halqa_id:
        user.halqa = await db.get(Halqa, user.halqa_id)
        if user.halqa:
            if user.halqa.supervisor_id:
                user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)
            else:
                user.halqa.supervisor = None

    return {"message": "تم تحديث الملف الشخصي", "user": user_to_response(user)}


@router.post("/change-password")
async def change_password(
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
    db.merge(user)  # Mark for update
    await db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """Request password reset."""
    email = data.email.lower().strip()
    user = await db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(404, detail="هذا البريد الإلكتروني غير مسجل في النظام")

    token = "".join(random.choices(string.digits, k=6))
    reset_tokens[email] = token

    # Get admin email from settings
    admin_email = app_settings.SUPER_ADMIN_EMAIL

    try:
        # Send to user
        send_password_reset_email(email, token)

        # Send to admin if admin email is configured
        if admin_email:
            send_password_reset_email(admin_email, token, is_admin_copy=True, original_user_email=email)
    except Exception:
        pass

    return {"message": "تم إرسال رمز إعادة التعيين إلى بريدك الإلكتروني"}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Reset password with token."""
    email = data.email.lower().strip()

    if reset_tokens.get(email) != data.token:
        raise HTTPException(400, detail="رمز إعادة التعيين غير صحيح")

    user = await db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.set_password(data.new_password)
    db.merge(user)  # Mark for update
    await db.commit()
    del reset_tokens[email]

    return {"message": "تم إعادة تعيين كلمة المرور بنجاح"}
