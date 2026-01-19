from pydantic import BaseModel, Field
from uuid import UUID
from typing import List
from app.models.event import MembershipStatusType
from app.schemas.event.common import OptionInfo, AdminInfo


# ============================================================================
# Entrance Code Entry Schema
# ============================================================================

class EntranceCodeEntryRequest(BaseModel):
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")


class EventEntryResponse(BaseModel):
    message: str
    event_id: UUID


# ============================================================================
# Event Overview Response Schema
# ============================================================================

class EventOverviewResponse(BaseModel):
    """이벤트 오버뷰 정보"""
    event: dict  # id, decision_subject, event_status, entrance_code
    options: List[OptionInfo]
    admin: AdminInfo
    participant_count: int
    membership_status: MembershipStatusType | None
    can_enter: bool
