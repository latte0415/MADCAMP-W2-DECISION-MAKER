from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.event import MembershipStatusType


class EventMembershipBase(BaseModel):
    membership_status: MembershipStatusType = MembershipStatusType.PENDING


class EventMembershipCreate(EventMembershipBase):
    user_id: UUID


class EventMembershipUpdate(BaseModel):
    membership_status: MembershipStatusType | None = None
    joined_at: datetime | None = None


class EventMembershipResponse(EventMembershipBase):
    id: UUID
    user_id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    joined_at: datetime | None = None

    class Config:
        from_attributes = True
