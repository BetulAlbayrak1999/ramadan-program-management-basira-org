import io
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings as app_settings
from app.models.user import User
from app.models.daily_card import DailyCard
from app.models.halqa import Halqa
from app.dependencies import RoleChecker
from typing import List
from pydantic import BaseModel
from app.schemas.user import (
    AdminUserUpdate, AdminResetPassword, SetRole,
    AssignHalqa, RejectRegistration, user_to_response,
)
from sqlalchemy import func
from app.schemas.halqa import HalqaCreate, HalqaUpdate, AssignMembers, halqa_to_response
from app.schemas.daily_card import card_to_response

router = APIRouter(prefix="/admin", tags=["admin"])

require_admin = RoleChecker("super_admin")


# ─── User Management ──────────────────────────────────────────────────────────


@router.get("/registrations")
async def get_registrations(
    status: str = Query("pending"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all pending registrations."""
    if status == "all":
        users = await db.query(User).order_by(User.created_at.desc()).all()
    else:
        users = await db.query(User).filter_by(status=status).order_by(User.created_at.desc()).all()

    # Load halqa for each user (D1 doesn't support eager loading)
    for user in users:
        if user.halqa_id:
            user.halqa = await db.get(Halqa, user.halqa_id)
            if user.halqa:
                if user.halqa.supervisor_id:
                    user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)
                else:
                    user.halqa.supervisor = None
        else:
            user.halqa = None

    return {"users": [user_to_response(u) for u in users]}


@router.post("/registration/{user_id}/approve")
async def approve_registration(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a registration request."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.status = "active"
    user.rejection_note = None
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

    return {"message": "تم قبول الطلب", "user": user_to_response(user)}


@router.post("/registration/{user_id}/reject")
async def reject_registration(
    user_id: int,
    data: RejectRegistration = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reject a registration request."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.status = "rejected"
    user.rejection_note = data.note if data else ""
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

    return {"message": "تم رفض الطلب", "user": user_to_response(user)}


@router.get("/users")
async def get_all_users(
    status: str = Query(None),
    gender: str = Query(None),
    halqa_id: int = Query(None),
    search: str = Query(""),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all users with optional filters."""
    try:
        print(f"DEBUG get_all_users: Starting with filters - status={status}, gender={gender}, halqa_id={halqa_id}, search={search}")
        query = db.query(User)

        if status:
            query = query.filter_by(status=status)
        if gender:
            query = query.filter_by(gender=gender)
        if halqa_id:
            query = query.filter_by(halqa_id=halqa_id)
        if search:
            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                )
            )

        print("DEBUG get_all_users: Executing query")
        users = await query.order_by(User.created_at.desc()).all()
        print(f"DEBUG get_all_users: Found {len(users)} users")

        # Load halqa for each user (D1 doesn't support eager loading)
        for idx, user in enumerate(users):
            try:
                print(f"DEBUG get_all_users: Processing user {idx+1}/{len(users)}, id={user.id}, halqa_id={user.halqa_id}")
                if user.halqa_id:
                    user.halqa = await db.get(Halqa, user.halqa_id)
                    if user.halqa:
                        if user.halqa.supervisor_id:
                            user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)
                        else:
                            user.halqa.supervisor = None
                    else:
                        print(f"WARNING: User {user.id} has halqa_id={user.halqa_id} but halqa not found")
                else:
                    user.halqa = None
            except Exception as e:
                print(f"ERROR loading halqa for user {user.id}: {type(e).__name__}: {str(e)}")
                import traceback
                print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
                # Set halqa to None to continue processing other users
                user.halqa = None

        print("DEBUG get_all_users: Building response")
        result = {"users": [user_to_response(u) for u in users]}
        print(f"DEBUG get_all_users: Response built successfully with {len(result['users'])} users")
        return result
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in get_all_users: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback_str
            }
        )


@router.get("/user/{user_id}")
async def get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user details."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    # Load halqa for response
    if user.halqa_id:
        user.halqa = await db.get(Halqa, user.halqa_id)
        # Load supervisor if halqa has one
        if user.halqa and user.halqa.supervisor_id:
            user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)

    return {"user": user_to_response(user)}


@router.put("/user/{user_id}")
async def update_user(
    user_id: int,
    data: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user details."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    allowed = ["full_name", "gender", "age", "phone", "country", "referral_source", "status", "halqa_id"]
    for field in allowed:
        value = getattr(data, field, None)
        if value is not None:
            setattr(user, field, value)

    db.merge(user)  # Mark for update
    await db.commit()
    await db.refresh(user)

    # Load halqa for response
    if user.halqa_id:
        user.halqa = await db.get(Halqa, user.halqa_id)
        if user.halqa and user.halqa.supervisor_id:
            user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)

    return {"message": "تم تحديث البيانات", "user": user_to_response(user)}


@router.post("/user/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    data: AdminResetPassword,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset user password by admin."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.set_password(data.new_password)
    db.merge(user)  # Mark for update
    await db.commit()
    return {"message": "تم إعادة تعيين كلمة المرور"}


@router.post("/user/{user_id}/withdraw")
async def withdraw_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Mark user as withdrawn."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.status = "withdrawn"
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

    return {"message": "تم سحب المشارك", "user": user_to_response(user)}


@router.post("/user/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Re-activate user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.status = "active"
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

    return {"message": "تم تفعيل المشارك", "user": user_to_response(user)}


# ─── Role Management ──────────────────────────────────────────────────────────


@router.post("/user/{user_id}/set-role")
async def set_user_role(
    user_id: int,
    data: SetRole,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Set user role (supervisor, super_admin, participant)."""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(404, detail="المستخدم غير موجود")

    if data.role not in ["participant", "supervisor", "super_admin"]:
        raise HTTPException(400, detail="الصلاحية غير صالحة")

    # Only primary admin can manage super_admin roles
    primary_email = app_settings.SUPER_ADMIN_EMAIL.lower()
    if data.role == "super_admin" or target.role == "super_admin":
        if admin.email != primary_email:
            raise HTTPException(403, detail="فقط المشرف الرئيسي يمكنه إدارة صلاحيات السوبر آدمن")

    target.role = data.role
    db.merge(target)  # Mark for update
    await db.commit()
    await db.refresh(target)

    # Load halqa for response
    if target.halqa_id:
        target.halqa = await db.get(Halqa, target.halqa_id)
        if target.halqa:
            if target.halqa.supervisor_id:
                target.halqa.supervisor = await db.get(User, target.halqa.supervisor_id)
            else:
                target.halqa.supervisor = None

    return {"message": "تم تحديث الصلاحية", "user": user_to_response(target)}


# ─── Halqa Management ─────────────────────────────────────────────────────────


@router.get("/halqas")
async def get_halqas(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all halqas."""
    try:
        print("DEBUG get_halqas: Starting to query halqas")
        halqas = await db.query(Halqa).all()
        print(f"DEBUG get_halqas: Found {len(halqas)} halqas")

        # Manually load supervisors and members for each halqa (D1 doesn't support eager loading)
        halqa_members_map = {}
        for idx, halqa in enumerate(halqas):
            print(f"DEBUG get_halqas: Processing halqa {idx+1}/{len(halqas)}, id={halqa.id}")
            print(f"DEBUG get_halqas: halqa.name = {halqa.name!r}, halqa.supervisor_id = {halqa.supervisor_id}")
            print(f"DEBUG get_halqas: halqa.__dict__ = {halqa.__dict__}")

            if halqa.supervisor_id:
                halqa.supervisor = await db.get(User, halqa.supervisor_id)
            else:
                halqa.supervisor = None

            # Load members for this halqa and store in map
            print(f"DEBUG get_halqas: Loading members for halqa id={halqa.id}")
            members = await db.query(User).filter_by(halqa_id=halqa.id).all()
            halqa_members_map[halqa.id] = members
            print(f"DEBUG get_halqas: Loaded {len(members)} members for halqa id={halqa.id}")

        print("DEBUG get_halqas: Building response")
        response = {"halqas": [halqa_to_response(h, halqa_members_map.get(h.id, [])) for h in halqas]}
        print("DEBUG get_halqas: Response built successfully")
        return response
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in get_halqas: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback_str
            }
        )


@router.post("/halqa")
async def create_halqa(
    data: HalqaCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new halqa."""
    name = data.name.strip()
    if not name:
        raise HTTPException(400, detail="اسم الحلقة مطلوب")

    if await db.query(Halqa).filter_by(name=name).first():
        raise HTTPException(400, detail="اسم الحلقة موجود مسبقاً")

    # Remove supervisor from any other halqa they currently supervise
    old_halqa_name = None
    if data.supervisor_id:
        old_halqa = await db.query(Halqa).filter_by(supervisor_id=data.supervisor_id).first()
        if old_halqa:
            old_halqa_name = old_halqa.name
            old_halqa.supervisor_id = None
            db.merge(old_halqa)  # Mark for update

    halqa = Halqa(name=name, supervisor_id=data.supervisor_id)
    db.add(halqa)
    await db.commit()
    await db.refresh(halqa)

    # Load supervisor and members for response
    if halqa.supervisor_id:
        halqa.supervisor = await db.get(User, halqa.supervisor_id)
    members = await db.query(User).filter_by(halqa_id=halqa.id).all()

    msg = "تم إنشاء الحلقة"
    if old_halqa_name:
        msg += f" (تم إزالة المشرف من حلقة «{old_halqa_name}»)"
    return {"message": msg, "halqa": halqa_to_response(halqa, members)}


@router.put("/halqa/{halqa_id}")
async def update_halqa(
    halqa_id: int,
    data: HalqaUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update halqa details."""
    try:
        print(f"DEBUG update_halqa: Starting update for halqa_id={halqa_id}")
        print(f"DEBUG update_halqa: data.name={data.name!r}, data.supervisor_id={data.supervisor_id}")

        halqa = await db.get(Halqa, halqa_id)
        if not halqa:
            raise HTTPException(404, detail="الحلقة غير موجودة")

        print(f"DEBUG update_halqa: Current halqa.name={halqa.name!r}, halqa.supervisor_id={halqa.supervisor_id}")

        if data.name is not None:
            # Validate name is not empty
            name = data.name.strip() if data.name else ""
            print(f"DEBUG update_halqa: Stripped name={name!r}")
            if not name:
                raise HTTPException(400, detail="اسم الحلقة مطلوب")
            print(f"DEBUG update_halqa: Setting halqa.name from {halqa.name!r} to {name!r}")
            halqa.name = name

        # Remove supervisor from any other halqa they currently supervise
        old_halqa_name = None
        if data.supervisor_id is not None:
            print(f"DEBUG update_halqa: Updating supervisor from {halqa.supervisor_id} to {data.supervisor_id}")
            if data.supervisor_id and data.supervisor_id != halqa.supervisor_id:
                old_halqa = await db.query(Halqa).filter(
                    Halqa.supervisor_id == data.supervisor_id, Halqa.id != halqa_id
                ).first()
                if old_halqa:
                    old_halqa_name = old_halqa.name
                    old_halqa.supervisor_id = None
                    db.merge(old_halqa)  # Mark for update
            halqa.supervisor_id = data.supervisor_id

        print(f"DEBUG update_halqa: About to merge halqa with name={halqa.name!r}")
        db.merge(halqa)  # Mark for update
        print("DEBUG update_halqa: About to commit")
        await db.commit()
        print("DEBUG update_halqa: Commit successful, about to refresh")
        await db.refresh(halqa)
        print(f"DEBUG update_halqa: After refresh, halqa.name={halqa.name!r}")

        # Load supervisor and members for response
        if halqa.supervisor_id:
            halqa.supervisor = await db.get(User, halqa.supervisor_id)
        members = await db.query(User).filter_by(halqa_id=halqa.id).all()

        msg = "تم تحديث الحلقة"
        if old_halqa_name:
            msg += f" (تم إزالة المشرف من حلقة «{old_halqa_name}»)"

        print(f"DEBUG update_halqa: Returning response with halqa.name={halqa.name!r}")
        return {"message": msg, "halqa": halqa_to_response(halqa, members)}
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in update_halqa: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback_str
            }
        )


@router.post("/halqa/{halqa_id}/assign-members")
async def assign_members_to_halqa(
    halqa_id: int,
    data: AssignMembers,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign members to a halqa."""
    halqa = await db.get(Halqa, halqa_id)
    if not halqa:
        raise HTTPException(404, detail="الحلقة غير موجودة")

    for uid in data.user_ids:
        user = await db.get(User, uid)
        if user:
            user.halqa_id = halqa_id
            db.merge(user)  # Mark for update

    await db.commit()
    return {"message": "تم تعيين المشاركين"}


@router.post("/user/{user_id}/assign-halqa")
async def assign_user_halqa(
    user_id: int,
    data: AssignHalqa,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign a single user to a halqa."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, detail="المستخدم غير موجود")

    user.halqa_id = data.halqa_id
    db.merge(user)  # Mark for update
    await db.commit()
    await db.refresh(user)

    # Load halqa for response
    if user.halqa_id:
        user.halqa = await db.get(Halqa, user.halqa_id)
        if user.halqa and user.halqa.supervisor_id:
            user.halqa.supervisor = await db.get(User, user.halqa.supervisor_id)

    return {"message": "تم تعيين الحلقة", "user": user_to_response(user)}


# ─── Analytics Dashboard ──────────────────────────────────────────────────────


async def _build_analytics_results(
    db: Session,
    gender: str = None,
    halqa_id: int = None,
    supervisor: str = None,
    member: str = None,
    min_pct: float = None,
    max_pct: float = None,
    period: str = "all",
    date_from: str = None,
    date_to: str = None,
    sort_by: str = "score",
    sort_order: str = "desc",
):
    """Shared helper for analytics and export."""
    query = db.query(User).filter_by(status="active")

    if gender:
        query = query.filter_by(gender=gender)
    if halqa_id:
        query = query.filter_by(halqa_id=halqa_id)
    if member:
        query = query.filter(User.full_name.ilike(f"%{member}%"))
    if supervisor:
        halqas = await db.query(Halqa).join(User, Halqa.supervisor_id == User.id).filter(
            User.full_name.ilike(f"%{supervisor}%")
        ).all()
        halqa_ids = [h.id for h in halqas]
        if halqa_ids:
            query = query.filter(User.halqa_id.in_(halqa_ids))

    users = await query.all()

    # Load halqa and supervisor for each user (D1 doesn't support eager loading)
    for u in users:
        if u.halqa_id:
            u.halqa = await db.get(Halqa, u.halqa_id)
            if u.halqa and u.halqa.supervisor_id:
                u.halqa.supervisor = await db.get(User, u.halqa.supervisor_id)

    # Date range
    today = date.today()
    start_date = None
    end_date = None

    if date_from:
        start_date = date.fromisoformat(date_from)
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start_date = today.replace(day=1)

    if date_to:
        end_date = date.fromisoformat(date_to)

    # Calculate max based on total days in range (not just submitted cards)
    max_per_day = len(DailyCard.SCORE_FIELDS) * 10  # 110
    total_days = None
    if start_date:
        range_end = end_date or today
        total_days = (range_end - start_date).days + 1

    results = []
    for u in users:
        card_query = db.query(DailyCard).filter_by(user_id=u.id)
        if start_date:
            card_query = card_query.filter(DailyCard.date >= start_date)
        if end_date:
            card_query = card_query.filter(DailyCard.date <= end_date)

        cards = await card_query.all()
        total = sum(c.total_score for c in cards)
        if total_days:
            max_total = total_days * max_per_day
        else:
            max_total = sum(c.max_score for c in cards) if cards else 0
        pct = round((total / max_total) * 100, 1) if max_total > 0 else 0

        if min_pct is not None and pct < min_pct:
            continue
        if max_pct is not None and pct > max_pct:
            continue

        results.append({
            "user_id": u.id,
            "member_id": u.member_id,
            "full_name": u.full_name,
            "gender": u.gender,
            "halqa_name": u.halqa.name if u.halqa else "بدون حلقة",
            "supervisor_name": u.halqa.supervisor.full_name if u.halqa and u.halqa.supervisor else "-",
            "total_score": total,
            "max_score": max_total,
            "percentage": pct,
            "cards_count": len(cards),
        })

    if sort_by == "name":
        results.sort(key=lambda x: x["full_name"], reverse=(sort_order == "desc"))
    elif sort_by == "percentage":
        results.sort(key=lambda x: x["percentage"], reverse=(sort_order == "desc"))
    else:
        results.sort(key=lambda x: x["total_score"], reverse=(sort_order == "desc"))

    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


@router.get("/analytics")
async def get_analytics(
    gender: str = Query(None),
    halqa_id: int = Query(None),
    supervisor: str = Query(None),
    member: str = Query(None),
    min_pct: float = Query(None),
    max_pct: float = Query(None),
    period: str = Query("all"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    sort_by: str = Query("score"),
    sort_order: str = Query("desc"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get comprehensive analytics."""
    results = await _build_analytics_results(
        db, gender=gender, halqa_id=halqa_id, supervisor=supervisor,
        member=member, min_pct=min_pct, max_pct=max_pct, period=period,
        date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order,
    )

    total_active = await db.query(User).filter_by(status="active").count()
    total_pending = await db.query(User).filter_by(status="pending").count()
    total_halqas = await db.query(Halqa).count()

    return {
        "results": results,
        "summary": {
            "total_active": total_active,
            "total_pending": total_pending,
            "total_halqas": total_halqas,
            "filtered_count": len(results),
        },
    }


@router.get("/user/{user_id}/cards")
async def get_user_cards(
    user_id: int,
    date_from: str = Query(None),
    date_to: str = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all daily cards for a specific user, with optional date filtering."""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(404, detail="المستخدم غير موجود")

    # Load halqa for response
    if target.halqa_id:
        target.halqa = await db.get(Halqa, target.halqa_id)
        if target.halqa and target.halqa.supervisor_id:
            target.halqa.supervisor = await db.get(User, target.halqa.supervisor_id)

    card_query = db.query(DailyCard).filter_by(user_id=user_id)
    if date_from:
        card_query = card_query.filter(DailyCard.date >= date.fromisoformat(date_from))
    if date_to:
        card_query = card_query.filter(DailyCard.date <= date.fromisoformat(date_to))

    cards = await card_query.order_by(DailyCard.date.desc()).all()
    return {
        "member": user_to_response(target),
        "cards": [card_to_response(c) for c in cards],
    }


# ─── Import / Export ──────────────────────────────────────────────────────────


@router.get("/export")
async def export_data(
    format: str = Query("csv"),
    gender: str = Query(None),
    halqa_id: int = Query(None),
    supervisor: str = Query(None),
    member: str = Query(None),
    min_pct: float = Query(None),
    max_pct: float = Query(None),
    period: str = Query("all"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    sort_by: str = Query("score"),
    sort_order: str = Query("desc"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export analytics data as CSV or XLSX with all applied filters."""
    import csv
    from openpyxl import Workbook

    results = await _build_analytics_results(
        db, gender=gender, halqa_id=halqa_id, supervisor=supervisor,
        member=member, min_pct=min_pct, max_pct=max_pct, period=period,
        date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order,
    )

    gender_map = {"male": "ذكر", "female": "أنثى"}
    rows = []
    for r in results:
        rows.append({
            "الترتيب": r["rank"],
            "رقم العضوية": r["member_id"],
            "الاسم": r["full_name"],
            "الجنس": gender_map.get(r["gender"], r["gender"]),
            "الحلقة": r["halqa_name"],
            "المشرف": r["supervisor_name"],
            "المجموع الحالي": r["total_score"],
            "المجموع العام": r["max_score"],
            "عدد البطاقات": r["cards_count"],
            "النسبة %": r["percentage"],
        })

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "النتائج"
        ws.sheet_view.rightToLeft = True

        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row[h] for h in headers])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=ramadan_results.xlsx"},
        )
    else:
        # UTF-8 BOM so Excel opens Arabic correctly
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        csv_bytes = "\ufeff" + output.getvalue()
        return Response(
            content=csv_bytes.encode("utf-8"),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": "attachment; filename=ramadan_results.csv"},
        )


@router.post("/import")
async def import_users(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Import users from Excel file."""
    from openpyxl import load_workbook

    wb = load_workbook(file.file)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]
    required_headers = ["الاسم", "الجنس", "العمر", "الهاتف", "البريد", "الدولة"]

    for h in required_headers:
        if h not in headers:
            raise HTTPException(400, detail=f"العمود {h} مفقود من الملف")

    last_user = await db.query(User).order_by(User.member_id.desc()).first()
    max_mid = last_user.member_id if last_user else None
    next_member_id = (max_mid + 1) if max_mid else 1000

    imported = 0
    errors = []
    seen_emails = set()

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # Skip completely empty rows
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue
        row_data = dict(zip(headers, row))
        try:
            raw_email = row_data.get("البريد")
            email = str(raw_email).lower().strip() if raw_email is not None else ""
            if not email or email == "none":
                errors.append(f"صف {row_idx}: البريد فارغ")
                continue
            if email in seen_emails:
                errors.append(f"صف {row_idx}: بريد مكرر في الملف")
                continue
            if await db.query(User).filter_by(email=email).first():
                errors.append(f"صف {row_idx}: البريد مسجل مسبقاً ({email})")
                continue

            seen_emails.add(email)
            raw_gender = str(row_data.get("الجنس", "")).strip()
            gender_map = {"ذكر": "male", "أنثى": "female", "male": "male", "female": "female"}
            gender = gender_map.get(raw_gender, raw_gender)

            raw_age = row_data.get("العمر", 0)
            age = int(raw_age) if raw_age is not None and str(raw_age).strip() else 0

            user = User(
                member_id=next_member_id,
                full_name=str(row_data.get("الاسم") or "").strip(),
                gender=gender,
                age=age,
                phone=str(row_data.get("الهاتف") or "").strip(),
                email=email,
                country=str(row_data.get("الدولة") or "").strip(),
                referral_source=str(row_data.get("المصدر") or "").strip(),
                status="pending",
                role="participant",
            )
            user.set_password("123456")  # Default password
            db.add(user)
            await db.flush()
            next_member_id += 1
            imported += 1
        except Exception as e:
            db.rollback()
            errors.append(f"صف {row_idx}: {str(e)}")

    await db.commit()
    return {
        "message": f"تم استيراد {imported} مشارك في قائمة الانتظار",
        "errors": errors,
    }


@router.get("/import-template")
async def get_import_template(
    admin: User = Depends(require_admin),
):
    """Download import template."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "قالب الاستيراد"
    ws.sheet_view.rightToLeft = True

    headers = ["الاسم", "الجنس", "العمر", "الهاتف", "البريد", "الدولة", "المصدر"]
    ws.append(headers)

    # Example row
    ws.append(["أحمد محمد علي", "ذكر", 25, "+966500000000", "ahmed@example.com", "السعودية", "صديق"])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=import_template.xlsx"},
    )


# ─── Bulk Actions ────────────────────────────────────────────────────────────


class BulkUserIds(BaseModel):
    user_ids: List[int]


class BulkAssignHalqa(BaseModel):
    user_ids: List[int]
    halqa_id: int | None = None


@router.post("/bulk/approve")
async def bulk_approve(
    data: BulkUserIds,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        count = 0
        print(f"DEBUG bulk_approve: Starting with {len(data.user_ids)} user_ids")
        for uid in data.user_ids:
            print(f"DEBUG bulk_approve: Processing user_id={uid}")
            u = await db.get(User, uid)
            if u:
                print(f"DEBUG bulk_approve: Found user {uid}, status={u.status}")
                if u.status == "pending":
                    u.status = "active"
                    u.rejection_note = None
                    db.merge(u)  # Mark for update
                    print(f"DEBUG bulk_approve: Merged user {uid} to active")
                    count += 1
            else:
                print(f"DEBUG bulk_approve: User {uid} not found")
        print(f"DEBUG bulk_approve: About to commit {count} updates")
        await db.commit()
        print(f"DEBUG bulk_approve: Commit successful")
        return {"message": f"تم قبول {count} طلب"}
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        print(f"ERROR in bulk_approve: {error_detail}")
        print(f"Traceback: {traceback_str}")
        # Return detailed error for debugging
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback_str
            }
        )


@router.post("/bulk/reject")
async def bulk_reject(
    data: BulkUserIds,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    count = 0
    for uid in data.user_ids:
        u = await db.get(User, uid)
        if u and u.status == "pending":
            u.status = "rejected"
            db.merge(u)  # Mark for update
            count += 1
    await db.commit()
    return {"message": f"تم رفض {count} طلب"}


@router.post("/bulk/activate")
async def bulk_activate(
    data: BulkUserIds,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    count = 0
    for uid in data.user_ids:
        u = await db.get(User, uid)
        if u and u.status in ("rejected", "withdrawn"):
            u.status = "active"
            db.merge(u)  # Mark for update
            count += 1
    await db.commit()
    return {"message": f"تم تفعيل {count} مشارك"}


@router.post("/bulk/withdraw")
async def bulk_withdraw(
    data: BulkUserIds,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    count = 0
    for uid in data.user_ids:
        u = await db.get(User, uid)
        if u and u.status == "active":
            u.status = "withdrawn"
            db.merge(u)  # Mark for update
            count += 1
    await db.commit()
    return {"message": f"تم سحب {count} مشارك"}


@router.post("/bulk/assign-halqa")
async def bulk_assign_halqa(
    data: BulkAssignHalqa,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    count = 0
    for uid in data.user_ids:
        u = await db.get(User, uid)
        if u:
            u.halqa_id = data.halqa_id
            db.merge(u)  # Mark for update
            count += 1
    await db.commit()
    return {"message": f"تم تعيين الحلقة لـ {count} م��ارك"}


# ─── Users Export ─────────────────────────────────────────────────────────────


@router.get("/export-users")
async def export_users(
    format: str = Query("xlsx"),
    status: str = Query(None),
    gender: str = Query(None),
    halqa_id: int = Query(None),
    search: str = Query(""),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export users list with all personal info."""
    import csv
    from openpyxl import Workbook

    query = db.query(User)
    if status:
        query = query.filter_by(status=status)
    if gender:
        male_values = {"male", "ذكر"}
        female_values = {"female", "أنثى"}
        match_set = male_values if gender == "male" else female_values
        query = query.filter(User.gender.in_(match_set))
    if halqa_id:
        query = query.filter_by(halqa_id=int(halqa_id))
    if search:
        query = query.filter(
            or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )

    users_list = await query.order_by(User.created_at.desc()).all()

    # Load halqa and supervisor for each user (D1 doesn't support eager loading)
    for u in users_list:
        if u.halqa_id:
            u.halqa = await db.get(Halqa, u.halqa_id)
            if u.halqa and u.halqa.supervisor_id:
                u.halqa.supervisor = await db.get(User, u.halqa.supervisor_id)

    gender_map = {"male": "ذكر", "female": "أنثى"}
    status_map = {"active": "نشط", "pending": "قيد المراجعة", "rejected": "مرفوض", "withdrawn": "منسحب"}
    role_map = {"participant": "مشارك", "supervisor": "مشرف", "super_admin": "سوبر آدمن"}

    rows = []
    for u in users_list:
        rows.append({
            "رقم العضوية": u.member_id,
            "الاسم": u.full_name,
            "الجنس": gender_map.get(u.gender, u.gender),
            "العمر": u.age,
            "الهاتف": u.phone,
            "البريد": u.email,
            "الدولة": u.country,
            "الحالة": status_map.get(u.status, u.status),
            "الصلاحية": role_map.get(u.role, u.role),
            "الحلقة": u.halqa.name if u.halqa else "-",
            "المشرف": u.halqa.supervisor.full_name if u.halqa and u.halqa.supervisor else "-",
            "مصدر التسجيل": u.referral_source or "",
            "تاريخ التسجيل": u.created_at.strftime("%Y-%m-%d") if u.created_at else "",
        })

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "المستخدمون"
        ws.sheet_view.rightToLeft = True
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row[h] for h in headers])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=users_report.xlsx"},
        )
    else:
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        csv_bytes = "\ufeff" + output.getvalue()
        return Response(
            content=csv_bytes.encode("utf-8"),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": "attachment; filename=users_report.csv"},
        )
