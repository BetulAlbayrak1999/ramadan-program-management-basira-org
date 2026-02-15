from datetime import date
from pydantic import BaseModel, Field


class DailyCardCreate(BaseModel):
    date: date
    quran: float = Field(default=0, ge=0, le=10)
    tadabbur: float = Field(default=0, ge=0, le=10)
    duas: float = Field(default=0, ge=0, le=10)
    taraweeh: float = Field(default=0, ge=0, le=10)
    tahajjud: float = Field(default=0, ge=0, le=10)
    duha: float = Field(default=0, ge=0, le=10)
    rawatib: float = Field(default=0, ge=0, le=10)
    main_lesson: float = Field(default=0, ge=0, le=10)
    enrichment_lesson: float = Field(default=0, ge=0, le=10)
    charity_worship: float = Field(default=0, ge=0, le=10)
    extra_work: float = Field(default=0, ge=0, le=10)
    extra_work_description: str = ""


def _to_isoformat(value):
    """Convert date/datetime to ISO format string. Handles both datetime objects and strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value  # Already a string (from D1)
    return value.isoformat()  # datetime object (from PostgreSQL)


def card_to_response(card) -> dict:
    """Build card response dict matching the frontend expected format."""
    return {
        "id": card.id,
        "tadabbur": card.tadabbur,
        "user_id": card.user_id,
        "date": _to_isoformat(card.date),
        "quran": card.quran,
        "duas": card.duas,
        "taraweeh": card.taraweeh,
        "tahajjud": card.tahajjud,
        "duha": card.duha,
        "rawatib": card.rawatib,
        "main_lesson": card.main_lesson,
        "enrichment_lesson": card.enrichment_lesson,
        "charity_worship": card.charity_worship,
        "extra_work": card.extra_work,
        "extra_work_description": card.extra_work_description,
        "total_score": card.total_score,
        "max_score": card.max_score,
        "percentage": card.percentage,
        "created_at": _to_isoformat(card.created_at),
        "updated_at": _to_isoformat(card.updated_at),
    }
