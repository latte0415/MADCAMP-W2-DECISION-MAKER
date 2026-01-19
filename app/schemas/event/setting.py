from pydantic import BaseModel, Field
from uuid import UUID
from typing import List
from app.schemas.event.common import OptionInfo


# ============================================================================
# Update Item Schemas
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


# ============================================================================
# Event Update Request Schema
# ============================================================================

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
# Event Setting Response Schema
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
