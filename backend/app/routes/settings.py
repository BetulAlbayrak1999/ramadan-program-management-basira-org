from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_settings import SiteSettings
from app.dependencies import RoleChecker
from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

require_admin = RoleChecker("super_admin")


@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    """Get site settings."""
    site = db.query(SiteSettings).first()
    if not site:
        return {"id": None, "enable_email_notifications": True}
    return {"id": site.id, "enable_email_notifications": site.enable_email_notifications}


@router.put("/")
def update_settings(
    data: SettingsUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update site settings."""
    site = db.query(SiteSettings).first()
    if not site:
        site = SiteSettings(enable_email_notifications=data.enable_email_notifications)
        db.add(site)
    else:
        site.enable_email_notifications = data.enable_email_notifications

    db.commit()
    db.refresh(site)
    return {
        "message": "تم تحديث الإعدادات",
        "settings": {
            "id": site.id,
            "enable_email_notifications": site.enable_email_notifications,
        },
    }
