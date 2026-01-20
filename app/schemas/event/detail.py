from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List
from app.models.event import EventStatusType
from app.models.proposal import ProposalStatusType, ProposalCategoryType
from app.schemas.event.common import OptionInfo


# ============================================================================
# Proposal Vote Info
# ============================================================================

class ProposalVoteInfo(BaseModel):
    """제안 투표 정보"""
    vote_count: int
    has_voted: bool  # 현재 사용자가 투표했는지 여부

    class Config:
        from_attributes = True


# ============================================================================
# Proposal Info Schemas
# ============================================================================

class AssumptionProposalInfo(BaseModel):
    """전제 제안 정보"""
    id: UUID
    assumption_id: UUID | None  # CREATION일 경우 None
    proposal_status: ProposalStatusType
    proposal_category: ProposalCategoryType
    proposal_content: str | None
    reason: str | None
    created_at: datetime
    created_by: UUID
    creator_name: str | None
    creator_email: str | None
    vote_info: ProposalVoteInfo

    class Config:
        from_attributes = True


class CriteriaProposalInfo(BaseModel):
    """기준 제안 정보"""
    id: UUID
    criteria_id: UUID | None  # CREATION일 경우 None
    proposal_status: ProposalStatusType
    proposal_category: ProposalCategoryType
    proposal_content: str | None
    reason: str | None
    created_at: datetime
    created_by: UUID
    creator_name: str | None
    creator_email: str | None
    vote_info: ProposalVoteInfo

    class Config:
        from_attributes = True


class ConclusionProposalInfo(BaseModel):
    """결론 제안 정보"""
    id: UUID
    criterion_id: UUID
    proposal_status: ProposalStatusType
    proposal_content: str
    created_at: datetime
    created_by: UUID
    creator_name: str | None
    creator_email: str | None
    vote_info: ProposalVoteInfo

    class Config:
        from_attributes = True


# ============================================================================
# Content with Proposals Schemas
# ============================================================================

class AssumptionWithProposals(BaseModel):
    """전제와 그에 대한 제안들"""
    id: UUID
    content: str
    is_deleted: bool  # 소프트 삭제 여부
    is_modified: bool  # 제안에 의해 수정되었는지
    original_content: str | None  # 원본 내용 (수정된 경우)
    modified_at: datetime | None  # 수정 시점 (applied_at)
    deleted_at: datetime | None  # 삭제 시점 (applied_at, is_deleted=True일 때)
    proposals: List[AssumptionProposalInfo]

    class Config:
        from_attributes = True


class CriterionWithProposals(BaseModel):
    """기준과 그에 대한 제안들 및 결론 제안들"""
    id: UUID
    content: str
    conclusion: str | None
    is_deleted: bool  # 소프트 삭제 여부
    is_modified: bool  # 제안에 의해 수정되었는지
    original_content: str | None  # 원본 내용 (수정된 경우)
    modified_at: datetime | None  # 수정 시점 (applied_at)
    deleted_at: datetime | None  # 삭제 시점 (applied_at, is_deleted=True일 때)
    proposals: List[CriteriaProposalInfo]
    conclusion_proposals: List[ConclusionProposalInfo]

    class Config:
        from_attributes = True


# ============================================================================
# Event Detail Response Schema
# ============================================================================

class EventDetailResponse(BaseModel):
    """이벤트 상세 조회 응답"""
    # 기본 정보
    id: UUID
    decision_subject: str
    event_status: EventStatusType
    is_admin: bool  # 현재 사용자가 관리자인지 여부
    
    # 선택지
    options: List[OptionInfo]
    
    # 전제와 제안들
    assumptions: List[AssumptionWithProposals]
    
    # 기준과 제안들, 결론 제안들
    criteria: List[CriterionWithProposals]
    
    # 전체 제안 (전제/기준에 연결되지 않은 CREATION 제안들)
    assumption_creation_proposals: List[AssumptionProposalInfo]
    criteria_creation_proposals: List[CriteriaProposalInfo]

    current_participants_count: int
    voted_participants_count: int

    class Config:
        from_attributes = True
