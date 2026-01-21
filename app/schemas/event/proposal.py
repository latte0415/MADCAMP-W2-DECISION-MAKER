from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import datetime
from app.models.proposal import ProposalStatusType, ProposalCategoryType
from app.exceptions import is_korean, translate_message


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
    
    @model_validator(mode='after')
    def translate_message(self):
        """언어 설정에 따라 메시지 번역"""
        if is_korean():
            self.message = translate_message(self.message)
        return self


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
    
    @model_validator(mode='after')
    def translate_message(self):
        """언어 설정에 따라 메시지 번역"""
        if is_korean():
            self.message = translate_message(self.message)
        return self


# ============================================================================
# Conclusion Proposal Schemas
# ============================================================================

class ConclusionProposalCreateRequest(BaseModel):
    """결론 제안 생성 요청"""
    proposal_content: str  # 필수
    # reason 없음, proposal_category 없음


class ConclusionProposalResponse(BaseModel):
    """결론 제안 응답"""
    id: UUID
    criterion_id: UUID
    proposal_status: ProposalStatusType
    proposal_content: str
    created_at: datetime
    created_by: UUID
    vote_count: int
    has_voted: bool

    class Config:
        from_attributes = True


class ConclusionProposalVoteResponse(BaseModel):
    """결론 제안 투표 응답"""
    message: str
    vote_id: UUID
    proposal_id: UUID
    vote_count: int

    class Config:
        from_attributes = True
    
    @model_validator(mode='after')
    def translate_message(self):
        """언어 설정에 따라 메시지 번역"""
        if is_korean():
            self.message = translate_message(self.message)
        return self


# ============================================================================
# Proposal Status Update Schemas
# ============================================================================

class ProposalStatusUpdateRequest(BaseModel):
    """제안 상태 변경 요청 (관리자용)"""
    status: ProposalStatusType  # ACCEPTED 또는 REJECTED만 허용
