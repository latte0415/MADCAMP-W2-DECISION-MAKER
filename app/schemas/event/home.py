from pydantic import BaseModel
from uuid import UUID
from app.models.event import EventStatusType, MembershipStatusType


class EventListItemResponse(BaseModel):
    """이벤트 리스트 항목"""
    id: UUID
    decision_subject: str
    event_status: EventStatusType
    admin_id: UUID
    admin_name: str | None  # User.email or None
    entrance_code: str
    participant_count: int
    is_admin: bool
    membership_status: MembershipStatusType | None

    class Config:
        from_attributes = True
