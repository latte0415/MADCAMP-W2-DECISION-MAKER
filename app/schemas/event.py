from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List
from app.models.event import EventStatusType, MembershipStatusType


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


class EntranceCodeEntryRequest(BaseModel):
    entrance_code: str = Field(..., min_length=6, max_length=6, pattern="^[A-Z0-9]{6}$")


class EventEntryResponse(BaseModel):
    message: str
    event_id: UUID


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


# ============================================================================
# Event List Response Schema
# ============================================================================

class EventListItemResponse(BaseModel):
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


# ============================================================================
# Event Overview Response Schema
# ============================================================================

class OptionInfo(BaseModel):
    id: UUID
    content: str

    class Config:
        from_attributes = True


class AdminInfo(BaseModel):
    id: UUID
    email: str

    class Config:
        from_attributes = True


class EventOverviewResponse(BaseModel):
    event: dict  # id, decision_subject, event_status, entrance_code
    options: List[OptionInfo]
    admin: AdminInfo
    participant_count: int
    membership_status: MembershipStatusType | None
    can_enter: bool


# ============================================================================
# Event Update Request Schema
# ============================================================================

class OptionUpdateItem(BaseModel):
    """선택지 업데이트 항목: id가 없으면 추가, 있으면 수정, null이면 삭제"""
    id: UUID | None = None  # None이면 추가, 있으면 수정
    content: str | None = None  # 삭제할 때는 None


class AssumptionUpdateItem(BaseModel):
    """전제 업데이트 항목: id가 없으면 추가, 있으면 수정, null이면 삭제"""
    id: UUID | None = None  # None이면 추가, 있으면 수정
    content: str | None = None  # 삭제할 때는 None


class CriterionUpdateItem(BaseModel):
    """기준 업데이트 항목: id가 없으면 추가, 있으면 수정, null이면 삭제"""
    id: UUID | None = None  # None이면 추가, 있으면 수정
    content: str | None = None  # 삭제할 때는 None


class EventUpdateRequest(BaseModel):
    """이벤트 정보 수정 요청 (모든 필드 optional)"""
    decision_subject: str | None = None
    options: List[OptionUpdateItem] | None = None
    assumptions: List[AssumptionUpdateItem] | None = None
    criteria: List[CriterionUpdateItem] | None = None
    max_membership: int | None = Field(None, gt=0)
    assumption_is_auto_approved_by_votes: bool | None = None
    assumption_min_votes_required: int | None = None
    criteria_is_auto_approved_by_votes: bool | None = None
    criteria_min_votes_required: int | None = None
    conclusion_approval_threshold_percent: int | None = Field(None, ge=1, le=100)
    membership_is_auto_approved: bool | None = None


# ============================================================================
# Membership Management Response Schemas
# ============================================================================

class MembershipResponse(BaseModel):
    """멤버십 승인/거부 응답"""
    message: str
    membership_id: UUID
    membership_status: MembershipStatusType

    class Config:
        from_attributes = True


class BulkMembershipResponse(BaseModel):
    """멤버십 일괄 처리 응답"""
    message: str
    approved_count: int | None = None
    rejected_count: int | None = None
    failed_count: int | None = None


# ============================================================================
# Event Setting Response Schema (편집용)
# ============================================================================

class AssumptionInfo(BaseModel):
    """전제 정보"""
    id: UUID
    content: str

    class Config:
        from_attributes = True


class CriterionInfo(BaseModel):
    """기준 정보"""
    id: UUID
    content: str

    class Config:
        from_attributes = True


class EventSettingResponse(BaseModel):
    """이벤트 설정 편집용 응답"""
    # 기본 정보
    decision_subject: str
    options: List[OptionInfo]
    assumptions: List[AssumptionInfo]
    criteria: List[CriterionInfo]
    max_membership: int
    # 투표 허용 정책
    assumption_is_auto_approved_by_votes: bool
    assumption_min_votes_required: int | None
    criteria_is_auto_approved_by_votes: bool
    criteria_min_votes_required: int | None
    conclusion_approval_threshold_percent: int | None
    # 입장 정책
    membership_is_auto_approved: bool
    entrance_code: str


# ============================================================================
# Membership List Response Schema
# ============================================================================

class MembershipListItemResponse(BaseModel):
    """멤버십 리스트 항목"""
    user_id: UUID
    membership_id: UUID
    status: MembershipStatusType
    created_at: datetime
    joined_at: datetime | None
    is_me: bool  # 본인 여부
    is_admin: bool  # 관리자 여부

    class Config:
        from_attributes = True
