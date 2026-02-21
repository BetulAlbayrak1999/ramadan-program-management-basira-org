from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.daily_card import DailyCard
from app.dependencies import get_active_user
from app.schemas.daily_card import DailyCardCreate, card_to_response

router = APIRouter(prefix="/api/participant", tags=["participant"])


@router.post("/card")
def save_card(
    data: DailyCardCreate,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """Create a daily card. Each date can only be submitted once (no editing)."""
    RAMADAN_START = date(2026, 2, 19)
    RAMADAN_END = date(2026, 3, 19)

    if data.date > date.today():
        raise HTTPException(400, detail="لا يمكن إدخال بطاقة بتاريخ مستقبلي")
    if data.date < RAMADAN_START or data.date > RAMADAN_END:
        raise HTTPException(400, detail="لا يمكن إدخال بطاقة خارج فترة البرنامج الرمضاني (19 فبراير - 19 مارس)")

    existing = db.query(DailyCard).filter_by(user_id=user.id, date=data.date).first()
    if existing:
        raise HTTPException(400, detail="تم إدخال بطاقة هذا اليوم مسبقاً ولا يمكن تعديلها")

    card = DailyCard(user_id=user.id, date=data.date)
    for field in DailyCard.SCORE_FIELDS:
        setattr(card, field, getattr(data, field, 0))
    card.extra_work_description = data.extra_work_description

    db.add(card)
    db.commit()
    db.refresh(card)
    return {"message": "تم حفظ البطاقة", "card": card_to_response(card)}


@router.get("/card/{card_date}")
def get_card(
    card_date: str,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """Get daily card for a specific date."""
    card = db.query(DailyCard).filter_by(
        user_id=user.id, date=date.fromisoformat(card_date)
    ).first()

    if not card:
        return {"card": None}
    return {"card": card_to_response(card)}


@router.get("/cards")
def get_all_cards(
    date_from: str = Query(None),
    date_to: str = Query(None),
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """Get all cards for current user, with optional date filtering."""
    query = db.query(DailyCard).filter_by(user_id=user.id)
    if date_from:
        query = query.filter(DailyCard.date >= date.fromisoformat(date_from))
    if date_to:
        query = query.filter(DailyCard.date <= date.fromisoformat(date_to))
    cards = query.order_by(DailyCard.date.desc()).all()
    return {"cards": [card_to_response(c) for c in cards]}


@router.get("/stats")
def get_stats(
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """Get participant statistics (no ranking info)."""
    today = date.today()

    # Today's card
    today_card = db.query(DailyCard).filter_by(user_id=user.id, date=today).first()
    today_percentage = today_card.percentage if today_card else 0

    # Overall stats
    all_cards = db.query(DailyCard).filter_by(user_id=user.id).all()
    overall_total = sum(c.total_score for c in all_cards)
    overall_max = sum(c.max_score for c in all_cards) if all_cards else 0
    overall_percentage = round((overall_total / overall_max) * 100, 1) if overall_max > 0 else 0

    # Supervisor info
    supervisor_info = None
    if user.halqa and user.halqa.supervisor:
        sup = user.halqa.supervisor
        supervisor_info = {
            "full_name": sup.full_name,
            "email": sup.email,
            "phone": sup.phone,
            "gender": sup.gender,
        }

    return {
        "today_percentage": today_percentage,
        "overall_percentage": overall_percentage,
        "overall_total": overall_total,
        "cards_count": len(all_cards),
        "supervisor": supervisor_info,
    }


