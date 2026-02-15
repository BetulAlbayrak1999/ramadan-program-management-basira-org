from pydantic import BaseModel, Field, field_validator
from typing import Optional


class HalqaCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Halqa name (required, non-empty)")
    supervisor_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('اسم الحلقة مطلوب ولا يمكن أن يكون فارغاً')
        return v.strip()


class HalqaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Halqa name (optional)")
    supervisor_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('اسم الحلقة لا يمكن أن يكون فارغاً')
        return v.strip() if v else None


class AssignMembers(BaseModel):
    user_ids: list[int] = []


def _to_isoformat(value):
    """Convert date/datetime to ISO format string. Handles both datetime objects and strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value  # Already a string (from D1)
    return value.isoformat()  # datetime object (from PostgreSQL)


def halqa_to_response(halqa, members=None) -> dict:
    """Build halqa response dict matching the frontend expected format."""
    # Use provided members list or fall back to halqa.members relationship
    members_list = members if members is not None else getattr(halqa, 'members', [])
    active_members = [m for m in members_list if m.status == "active"]
    male_values = {"male", "ذكر"}
    return {
        "id": halqa.id,
        "name": halqa.name,
        "supervisor_id": halqa.supervisor_id,
        "supervisor_name": halqa.supervisor.full_name if halqa.supervisor else None,
        "member_count": len(active_members),
        "male_count": len([m for m in active_members if m.gender in male_values]),
        "female_count": len([m for m in active_members if m.gender not in male_values]),
        "created_at": _to_isoformat(halqa.created_at),
        "updated_at": _to_isoformat(halqa.updated_at),
    }
