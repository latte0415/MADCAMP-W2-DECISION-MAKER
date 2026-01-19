from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.proposal import ProposalStatusType, ProposalCategoryType


# ============================================================================
# Request Schemas
# ============================================================================

class AssumptionProposalCreateRequest(BaseModel):
    """전제 제안 생성 요청"""
    proposal_category: ProposalCategoryType
    assumption_id: UUID | None = None  # MODIFICATION/DELETION일 때 필수
    proposal_content: str | None = None  # CREATION/MODIFICATION일 때 필수
    reason: str | None = None


# ============================================================================
# Response Schemas
# ============================================================================

class AssumptionProposalResponse(BaseModel):
    """전제 제안 응답"""
    id: UUID
    event_id: UUID
    assumption_id: UUID | None
    proposal_status: ProposalStatusType
    proposal_category: ProposalCategoryType
    proposal_content: str | None
    reason: str | None
    created_at: datetime
    created_by: UUID
    vote_count: int
    has_voted: bool

    class Config:
        from_attributes = True


class AssumptionProposalVoteResponse(BaseModel):
    """전제 제안 투표 응답"""
    message: str
    vote_id: UUID
    proposal_id: UUID
    vote_count: int

    class Config:
        from_attributes = True


# ============================================================================
# Criteria Proposal Schemas
# ============================================================================

class CriteriaProposalCreateRequest(BaseModel):
    """기준 제안 생성 요청"""
    proposal_category: ProposalCategoryType
    criteria_id: UUID | None = None  # MODIFICATION/DELETION일 때 필수
    proposal_content: str | None = None  # CREATION/MODIFICATION일 때 필수
    reason: str | None = None


class CriteriaProposalResponse(BaseModel):
    """기준 제안 응답"""
    id: UUID
    event_id: UUID
    criteria_id: UUID | None
    proposal_status: ProposalStatusType
    proposal_category: ProposalCategoryType
    proposal_content: str | None
    reason: str | None
    created_at: datetime
    created_by: UUID
    vote_count: int
    has_voted: bool

    class Config:
        from_attributes = True


class CriteriaProposalVoteResponse(BaseModel):
    """기준 제안 투표 응답"""
    message: str
    vote_id: UUID
    proposal_id: UUID
    vote_count: int

    class Config:
        from_attributes = True
