from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List
from app.models.event import EventStatusType


# ============================================================================
# Attach Request Schemas (for options, assumptions, criteria)
# ============================================================================

class OptionAttachRequest(BaseModel):
    content: str


class AssumptionAttachRequest(BaseModel):
    content: str


class CriterionAttachRequest(BaseModel):
    content: str


# ============================================================================
# Entrance Code Schemas
# ============================================================================

class EntranceCodeCheckRequest(BaseModel):
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")


class EntranceCodeCheckResponse(BaseModel):
    entrance_code: str
    is_available: bool


class EntranceCodeGenerateResponse(BaseModel):
    code: str


# ============================================================================
# Event Creation Request Schema
# ============================================================================

class EventCreateRequest(BaseModel):
    decision_subject: str
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")
    assumption_is_auto_approved_by_votes: bool = True
    criteria_is_auto_approved_by_votes: bool = True
    membership_is_auto_approved: bool = True
    conclusion_is_auto_approved_by_votes: bool = True
    assumption_min_votes_required: int | None = None
    criteria_min_votes_required: int | None = None
    conclusion_approval_threshold_percent: int | None = Field(None, ge=1, le=100)
    max_membership: int = Field(..., gt=0)
    options: List[OptionAttachRequest] = Field(default_factory=list)
    assumptions: List[AssumptionAttachRequest] = Field(default_factory=list)
    criteria: List[CriterionAttachRequest] = Field(default_factory=list)


# ============================================================================
# Event Response Schema
# ============================================================================

class EventResponse(BaseModel):
    id: UUID
    decision_subject: str
    entrance_code: str
    assumption_is_auto_approved_by_votes: bool
    criteria_is_auto_approved_by_votes: bool
    membership_is_auto_approved: bool
    conclusion_is_auto_approved_by_votes: bool
    assumption_min_votes_required: int | None
    criteria_min_votes_required: int | None
    conclusion_approval_threshold_percent: int | None
    event_status: EventStatusType
    max_membership: int
    admin_id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
