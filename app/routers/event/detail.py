from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models import User
from app.services.event.proposal_service import ProposalService
from app.services.event import EventService
from app.schemas.event import (
    EventDetailResponse,
    AssumptionProposalCreateRequest,
    AssumptionProposalResponse,
    AssumptionProposalVoteResponse,
    CriteriaProposalCreateRequest,
    CriteriaProposalResponse,
    CriteriaProposalVoteResponse,
    ConclusionProposalCreateRequest,
    ConclusionProposalResponse,
    ConclusionProposalVoteResponse,
)
from app.schemas.event.proposal import ProposalStatusUpdateRequest
from app.dependencies.auth import get_current_user
from app.dependencies.services import (
    get_event_service,
    get_proposal_service,
)


router = APIRouter(tags=["events-detail"])


@router.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event_detail(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
    """
    이벤트 상세 조회 API (Event 4-0-0 페이지용)
    - 주제, 선택지, 전제, 기준, 각각에 대한 제안 조회
    - 각 제안에 대한 투표 정보 포함
    - ACCEPTED 멤버십만 조회 가능
    """
    return event_service.get_event_detail(
        event_id=event_id,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/assumption-proposals",
    response_model=AssumptionProposalResponse,
    status_code=status.HTTP_201_CREATED
)
def create_assumption_proposal(
    event_id: UUID,
    request: AssumptionProposalCreateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> AssumptionProposalResponse:
    """
    전제 제안 생성 API
    - IN_PROGRESS 상태에서만 가능
    - ACCEPTED 멤버십 필요
    """
    return proposal_service.create_assumption_proposal(
        event_id=event_id,
        request=request,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/assumption-proposals/{proposal_id}/votes",
    response_model=AssumptionProposalVoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_assumption_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> AssumptionProposalVoteResponse:
    """
    전제 제안 투표 생성 API
    - IN_PROGRESS 상태에서만 가능
    - PENDING 제안에만 투표 가능
    """
    return proposal_service.create_assumption_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


@router.delete(
    "/events/{event_id}/assumption-proposals/{proposal_id}/votes",
    response_model=AssumptionProposalVoteResponse
)
def delete_assumption_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> AssumptionProposalVoteResponse:
    """
    전제 제안 투표 삭제 API
    - IN_PROGRESS 상태에서만 가능
    - 본인 투표만 삭제 가능
    """
    return proposal_service.delete_assumption_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/criteria-proposals",
    response_model=CriteriaProposalResponse,
    status_code=status.HTTP_201_CREATED
)
def create_criteria_proposal(
    event_id: UUID,
    request: CriteriaProposalCreateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> CriteriaProposalResponse:
    """
    기준 제안 생성 API
    - IN_PROGRESS 상태에서만 가능
    - ACCEPTED 멤버십 필요
    """
    return proposal_service.create_criteria_proposal(
        event_id=event_id,
        request=request,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/criteria-proposals/{proposal_id}/votes",
    response_model=CriteriaProposalVoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_criteria_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> CriteriaProposalVoteResponse:
    """
    기준 제안 투표 생성 API
    - IN_PROGRESS 상태에서만 가능
    - PENDING 제안에만 투표 가능
    """
    return proposal_service.create_criteria_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


@router.delete(
    "/events/{event_id}/criteria-proposals/{proposal_id}/votes",
    response_model=CriteriaProposalVoteResponse
)
def delete_criteria_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> CriteriaProposalVoteResponse:
    """
    기준 제안 투표 삭제 API
    - IN_PROGRESS 상태에서만 가능
    - 본인 투표만 삭제 가능
    """
    return proposal_service.delete_criteria_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/criteria/{criterion_id}/conclusion-proposals",
    response_model=ConclusionProposalResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conclusion_proposal(
    event_id: UUID,
    criterion_id: UUID,
    request: ConclusionProposalCreateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ConclusionProposalResponse:
    """
    결론 제안 생성 API
    - IN_PROGRESS 상태에서만 가능
    - ACCEPTED 멤버십 필요
    """
    return proposal_service.create_conclusion_proposal(
        event_id=event_id,
        criterion_id=criterion_id,
        request=request,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/conclusion-proposals/{proposal_id}/votes",
    response_model=ConclusionProposalVoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conclusion_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ConclusionProposalVoteResponse:
    """
    결론 제안 투표 생성 API
    - IN_PROGRESS 상태에서만 가능
    - PENDING 제안에만 투표 가능
    """
    return proposal_service.create_conclusion_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


@router.delete(
    "/events/{event_id}/conclusion-proposals/{proposal_id}/votes",
    response_model=ConclusionProposalVoteResponse
)
def delete_conclusion_proposal_vote(
    event_id: UUID,
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ConclusionProposalVoteResponse:
    """
    결론 제안 투표 삭제 API
    - IN_PROGRESS 상태에서만 가능
    - 본인 투표만 삭제 가능
    """
    return proposal_service.delete_conclusion_proposal_vote(
        event_id=event_id,
        proposal_id=proposal_id,
        user_id=current_user.id
    )


# ============================================================================
# Admin Proposal Status Update APIs
# ============================================================================

@router.patch(
    "/events/{event_id}/assumption-proposals/{proposal_id}/status",
    response_model=AssumptionProposalResponse
)
def update_assumption_proposal_status(
    event_id: UUID,
    proposal_id: UUID,
    request: ProposalStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> AssumptionProposalResponse:
    """
    전제 제안 상태 변경 API (관리자용)
    - 관리자 권한 필요
    - PENDING 상태만 변경 가능
    - ACCEPTED 시 제안 자동 적용
    """
    return proposal_service.update_assumption_proposal_status(
        event_id=event_id,
        proposal_id=proposal_id,
        status=request.status,
        user_id=current_user.id
    )


@router.patch(
    "/events/{event_id}/criteria-proposals/{proposal_id}/status",
    response_model=CriteriaProposalResponse
)
def update_criteria_proposal_status(
    event_id: UUID,
    proposal_id: UUID,
    request: ProposalStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> CriteriaProposalResponse:
    """
    기준 제안 상태 변경 API (관리자용)
    - 관리자 권한 필요
    - PENDING 상태만 변경 가능
    - ACCEPTED 시 제안 자동 적용
    """
    return proposal_service.update_criteria_proposal_status(
        event_id=event_id,
        proposal_id=proposal_id,
        status=request.status,
        user_id=current_user.id
    )


@router.patch(
    "/events/{event_id}/conclusion-proposals/{proposal_id}/status",
    response_model=ConclusionProposalResponse
)
def update_conclusion_proposal_status(
    event_id: UUID,
    proposal_id: UUID,
    request: ProposalStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ConclusionProposalResponse:
    """
    결론 제안 상태 변경 API (관리자용)
    - 관리자 권한 필요
    - PENDING 상태만 변경 가능
    - ACCEPTED 시 제안 자동 적용
    """
    return proposal_service.update_conclusion_proposal_status(
        event_id=event_id,
        proposal_id=proposal_id,
        status=request.status,
        user_id=current_user.id
    )
