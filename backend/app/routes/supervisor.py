import io
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.daily_card import DailyCard
from app.models.halqa import Halqa
from app.dependencies import RoleChecker
from app.schemas.user import user_to_response
from app.schemas.daily_card import DailyCardCreate, card_to_response
from app.schemas.halqa import halqa_to_response

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

MAX_PER_DAY = len(DailyCard.SCORE_FIELDS) * 10  # 110
RAMADAN_START = date(2026, 2, 19)
RAMADAN_END = date(2026, 3, 19)

require_supervisor = RoleChecker("supervisor", "super_admin")


def _resolve_halqa(user, db, halqa_id=None):
    """Resolve which halqa to use.
    - super_admin: can pick any halqa via halqa_id, or None for all members.
    - supervisor: always uses their own halqa (halqa_id ignored).
    """
    if user.role == "super_admin":
        if halqa_id:
            halqa = db.get(Halqa, halqa_id)
            if not halqa:
                raise HTTPException(404, detail="الحلقة غير موجودة")
            return halqa
        return None  # means "all halqas"
    # Regular supervisor
    halqa = db.query(Halqa).filter_by(supervisor_id=user.id).first()
    if not halqa:
        raise HTTPException(404, detail="لا توجد حلقة مسندة إليك")
    return halqa


def _get_members(db, halqa):
    """Get active members for a halqa, or all active participants if halqa is None."""
    if halqa:
        return db.query(User).filter_by(halqa_id=halqa.id, status="active").all()
    return db.query(User).filter_by(status="active", role="participant").all()


def _verify_member_access(user, member_id, db):
    """Verify the supervisor/admin can access this member."""
    member = db.get(User, member_id)
    if not member:
        raise HTTPException(404, detail="المشارك غير موجود")
    if user.role == "super_admin":
        return member
    halqa = db.query(Halqa).filter_by(supervisor_id=user.id).first()
    if not halqa or member.halqa_id != halqa.id:
        raise HTTPException(403, detail="المشارك ليس في حلقتك")
    return member


@router.get("/halqas")
def get_all_halqas(
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get halqas available to this user. Super admin sees all, supervisor sees own."""
    if user.role == "super_admin":
        halqas = db.query(Halqa).all()
    else:
        halqa = db.query(Halqa).filter_by(supervisor_id=user.id).first()
        halqas = [halqa] if halqa else []
    return {"halqas": [halqa_to_response(h) for h in halqas]}


@router.get("/members")
def get_halqa_members(
    halqa_id: int = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get members. Super admin can filter by halqa_id or see all."""
    halqa = _resolve_halqa(user, db, halqa_id)
    members = _get_members(db, halqa)
    return {
        "halqa": halqa_to_response(halqa) if halqa else None,
        "members": [user_to_response(m) for m in members],
    }


@router.get("/member/{member_id}/cards")
def get_member_cards(
    member_id: int,
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get all cards for a specific member."""
    member = _verify_member_access(user, member_id, db)
    cards = db.query(DailyCard).filter_by(user_id=member_id).order_by(DailyCard.date.desc()).all()
    return {
        "member": user_to_response(member),
        "cards": [card_to_response(c) for c in cards],
    }


@router.get("/member/{member_id}/card/{card_date}")
def get_member_card_detail(
    member_id: int,
    card_date: str,
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get a specific daily card for a member (full detail)."""
    member = _verify_member_access(user, member_id, db)
    card = db.query(DailyCard).filter_by(
        user_id=member_id, date=date.fromisoformat(card_date)
    ).first()

    if not card:
        return {"member": user_to_response(member), "card": None}
    return {"member": user_to_response(member), "card": card_to_response(card)}


@router.put("/member/{member_id}/card/{card_date}")
def update_member_card(
    member_id: int,
    card_date: str,
    data: DailyCardCreate,
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Create or update a daily card for a member."""
    member = _verify_member_access(user, member_id, db)

    target_date = date.fromisoformat(card_date)
    if target_date > date.today():
        raise HTTPException(400, detail="لا يمكن إدخال بطاقة بتاريخ مستقبلي")
    if target_date < RAMADAN_START or target_date > RAMADAN_END:
        raise HTTPException(400, detail="البطاقات مسموحة فقط خلال شهر رمضان")

    card = db.query(DailyCard).filter_by(user_id=member_id, date=target_date).first()
    if not card:
        card = DailyCard(user_id=member_id, date=target_date)
        db.add(card)

    for field in DailyCard.SCORE_FIELDS:
        setattr(card, field, getattr(data, field, 0))
    card.extra_work_description = data.extra_work_description

    db.commit()
    db.refresh(card)
    return {"message": "تم تحديث بطاقة المشارك", "card": card_to_response(card)}


@router.delete("/member/{member_id}/card/{card_date}")
def delete_member_card(
    member_id: int,
    card_date: str,
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Delete a daily card for a member."""
    _verify_member_access(user, member_id, db)
    target_date = date.fromisoformat(card_date)
    card = db.query(DailyCard).filter_by(user_id=member_id, date=target_date).first()
    if not card:
        raise HTTPException(404, detail="البطاقة غير موجودة")
    db.delete(card)
    db.commit()
    return {"message": "تم حذف البطاقة بنجاح"}


@router.get("/leaderboard")
def get_leaderboard(
    halqa_id: int = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get leaderboard. Super admin can filter by halqa or see all."""
    halqa = _resolve_halqa(user, db, halqa_id)
    members = _get_members(db, halqa)

    today = date.today()
    elapsed_days = max((min(today, RAMADAN_END) - RAMADAN_START).days + 1, 1)

    leaderboard = []
    for m in members:
        cards = db.query(DailyCard).filter_by(user_id=m.id).all()
        total = sum(c.total_score for c in cards)
        max_total = elapsed_days * MAX_PER_DAY
        pct = round((total / max_total) * 100, 1) if max_total > 0 else 0
        leaderboard.append({
            "user_id": m.id,
            "member_id": m.member_id,
            "full_name": m.full_name,
            "gender": m.gender,
            "halqa_name": m.halqa.name if m.halqa else "-",
            "total_score": total,
            "percentage": pct,
            "cards_count": len(cards),
        })

    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    return {
        "halqa": halqa_to_response(halqa) if halqa else None,
        "leaderboard": leaderboard,
    }


@router.get("/daily-summary")
def get_daily_summary(
    halqa_id: int = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
    date_param: str = Query(None, alias="date"),
):
    """Get daily submission summary. Super admin can filter by halqa."""
    target_date_str = date_param or date.today().isoformat()
    target_date = date.fromisoformat(target_date_str)

    halqa = _resolve_halqa(user, db, halqa_id)
    members = _get_members(db, halqa)

    submitted = []
    not_submitted = []

    for member in members:
        card = db.query(DailyCard).filter_by(user_id=member.id, date=target_date).first()
        if card:
            submitted.append({
                "member": user_to_response(member),
                "card": card_to_response(card),
            })
        else:
            not_submitted.append(user_to_response(member))

    return {
        "date": target_date.isoformat(),
        "halqa": halqa_to_response(halqa) if halqa else None,
        "submitted": submitted,
        "not_submitted": not_submitted,
        "submitted_count": len(submitted),
        "not_submitted_count": len(not_submitted),
        "total_members": len(members),
    }


@router.get("/range-summary")
def get_range_summary(
    halqa_id: int = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get summary for a custom date range."""
    today = date.today()
    start = date.fromisoformat(date_from) if date_from else today - timedelta(days=6)
    end = date.fromisoformat(date_to) if date_to else today
    total_days = (end - start).days + 1

    halqa = _resolve_halqa(user, db, halqa_id)
    members = _get_members(db, halqa)
    summary = []

    for member in members:
        cards = db.query(DailyCard).filter(
            DailyCard.user_id == member.id,
            DailyCard.date >= start,
            DailyCard.date <= end,
        ).all()

        total = sum(c.total_score for c in cards)
        max_total = total_days * MAX_PER_DAY
        pct = round((total / max_total) * 100, 1) if max_total > 0 else 0

        sup = member.halqa.supervisor if member.halqa and member.halqa.supervisor else None
        summary.append({
            "member": user_to_response(member),
            "cards_submitted": len(cards),
            "total_days": total_days,
            "total_score": total,
            "percentage": pct,
            "supervisor_name": sup.full_name if sup else "-",
        })

    summary.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "halqa": halqa_to_response(halqa) if halqa else None,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "total_days": total_days,
        "summary": summary,
    }


@router.get("/weekly-summary")
def get_weekly_summary(
    halqa_id: int = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Get weekly summary. Super admin can filter by halqa."""
    halqa = _resolve_halqa(user, db, halqa_id)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    members = _get_members(db, halqa)
    summary = []

    week_days = (today - week_start).days + 1

    for member in members:
        cards = db.query(DailyCard).filter(
            DailyCard.user_id == member.id,
            DailyCard.date >= week_start,
            DailyCard.date <= today,
        ).all()

        total = sum(c.total_score for c in cards)
        max_total = week_days * MAX_PER_DAY
        pct = round((total / max_total) * 100, 1) if max_total > 0 else 0

        summary.append({
            "member": user_to_response(member),
            "cards_submitted": len(cards),
            "total_score": total,
            "percentage": pct,
        })

    summary.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "halqa": halqa_to_response(halqa) if halqa else None,
        "week_start": week_start.isoformat(),
        "week_end": today.isoformat(),
        "summary": summary,
    }


@router.get("/export")
def export_cards(
    format: str = Query("xlsx"),
    halqa_id: int = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search_name: str = Query(None),
    search_gender: str = Query(None),
    user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """Export detailed daily card report as CSV or XLSX."""
    import csv
    from openpyxl import Workbook

    today = date.today()
    start = date.fromisoformat(date_from) if date_from else RAMADAN_START
    end = date.fromisoformat(date_to) if date_to else today

    halqa = _resolve_halqa(user, db, halqa_id)
    members = _get_members(db, halqa)

    # Apply search filters
    if search_name:
        members = [m for m in members if search_name in m.full_name]
    if search_gender:
        male_values = {"male", "ذكر"}
        female_values = {"female", "أنثى"}
        match_set = male_values if search_gender == "male" else female_values
        members = [m for m in members if m.gender in match_set]

    gender_map = {"male": "ذكر", "female": "أنثى"}
    rows = []
    for member in members:
        cards = db.query(DailyCard).filter(
            DailyCard.user_id == member.id,
            DailyCard.date >= start,
            DailyCard.date <= end,
        ).order_by(DailyCard.date).all()

        halqa_name = member.halqa.name if member.halqa else "-"
        for c in cards:
            rows.append({
                "رقم العضوية": member.member_id,
                "الاسم": member.full_name,
                "الجنس": gender_map.get(member.gender, member.gender),
                "الحلقة": halqa_name,
                "التاريخ": c.date.isoformat(),
                "وِرد القرآن": c.quran,
                "الأدعية": c.duas,
                "صلاة التراويح": c.taraweeh,
                "التهجد والوتر": c.tahajjud,
                "صلاة الضحى": c.duha,
                "السنن الرواتب": c.rawatib,
                "المقطع الأساسي": c.main_lesson,
                "المقطع الواجب": c.required_lesson,
                "المقطع الإثرائي": c.enrichment_lesson,
                "عبادة متعدية": c.charity_worship,
                "أعمال إضافية": c.extra_work,
                "وصف الأعمال الإضافية": c.extra_work_description or "",
                "المجموع": c.total_score,
                "النسبة %": c.percentage,
            })

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "البطاقات اليومية"
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
            headers={"Content-Disposition": "attachment; filename=daily_cards_report.xlsx"},
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
            headers={"Content-Disposition": "attachment; filename=daily_cards_report.csv"},
        )
