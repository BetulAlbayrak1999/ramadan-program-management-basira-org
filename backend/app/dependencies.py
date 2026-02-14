from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
# Use lightweight JWT implementation instead of python-jose
from app.utils.jwt_hs256 import jwt, JWTError

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Decode JWT and return the current user."""
    from app.models.user import User

    if credentials is None:
        raise HTTPException(status_code=401, detail="التوكن مطلوب")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="التوكن غير صالح")
    except JWTError:
        raise HTTPException(status_code=401, detail="التوكن غير صالح أو منتهي الصلاحية")

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return user


def get_active_user(user=Depends(get_current_user)):
    """Ensure user is active."""
    if user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل")
    return user


class RoleChecker:
    """Callable dependency for role-based access."""

    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    def __call__(self, user=Depends(get_current_user)):
        if user.status != "active" and user.role != "super_admin":
            raise HTTPException(status_code=403, detail="الحساب غير مفعل")
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية للوصول")
        return user


def create_access_token(user_id: int) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES)
    # Convert datetime to Unix timestamp (int) for JSON serialization
    payload = {"sub": str(user_id), "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
