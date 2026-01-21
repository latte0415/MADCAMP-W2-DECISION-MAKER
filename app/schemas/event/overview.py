from pydantic import BaseModel, Field, model_validator
from uuid import UUID
from typing import List
from app.models.event import MembershipStatusType
from app.schemas.event.common import OptionInfo, AdminInfo
from app.exceptions import is_korean, translate_message


# ============================================================================
# Entrance Code Entry Schema
# ============================================================================

class EntranceCodeEntryRequest(BaseModel):
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")


class EventEntryResponse(BaseModel):
    message: str
    event_id: UUID
    
    @model_validator(mode='after')
    def translate_message(self):
        """언어 설정에 따라 메시지 번역"""
        if is_korean():
            self.message = translate_message(self.message)
        return self


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
