from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.event import EventStatusType


class EventBase(BaseModel):
    decision_subject: str
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")
    assumption_is_auto_approved_by_votes: bool = True
    criteria_is_auto_approved_by_votes: bool = True
    membership_is_auto_approved: bool = True
    conclusion_is_auto_approved_by_votes: bool = True
    assumption_min_votes_required: int | None = None
    criteria_min_votes_required: int | None = None
    conclusion_approval_threshold_percent: int | None = Field(None, ge=1, le=100)
    event_status: EventStatusType = EventStatusType.NOT_STARTED
    max_membership: int = Field(..., gt=0)
    admin_id: UUID


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    decision_subject: str | None = None
    assumption_is_auto_approved_by_votes: bool | None = None
    criteria_is_auto_approved_by_votes: bool | None = None
    membership_is_auto_approved: bool | None = None
    conclusion_is_auto_approved_by_votes: bool | None = None
    assumption_min_votes_required: int | None = None
    criteria_min_votes_required: int | None = None
    conclusion_approval_threshold_percent: int | None = Field(None, ge=1, le=100)
    event_status: EventStatusType | None = None
    max_membership: int | None = Field(None, gt=0)


class EventResponse(EventBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
