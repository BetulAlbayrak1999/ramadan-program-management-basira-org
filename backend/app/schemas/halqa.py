from pydantic import BaseModel
from typing import Optional


class HalqaCreate(BaseModel):
    name: str
    supervisor_id: Optional[int] = None


class HalqaUpdate(BaseModel):
    name: Optional[str] = None
    supervisor_id: Optional[int] = None


class AssignMembers(BaseModel):
    user_ids: list[int] = []


def halqa_to_response(halqa) -> dict:
    """Build halqa response dict matching the frontend expected format."""
    active_members = [m for m in halqa.members if m.status == "active"]
    male_values = {"male", "ذكر"}
    return {
        "id": halqa.id,
        "name": halqa.name,
        "supervisor_id": halqa.supervisor_id,
        "supervisor_name": halqa.supervisor.full_name if halqa.supervisor else None,
        "member_count": len(active_members),
        "male_count": len([m for m in active_members if m.gender in male_values]),
        "female_count": len([m for m in active_members if m.gender not in male_values]),
        "created_at": halqa.created_at.isoformat() if halqa.created_at else None,
    }
