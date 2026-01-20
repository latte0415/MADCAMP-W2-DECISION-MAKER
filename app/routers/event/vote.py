from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models import User
from app.services.event.vote_service import VoteService
from app.schemas.event.vote import (
    VoteCreateRequest,
    VoteResponse,
    VoteViewResponse,
    VoteResultResponse,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_vote_service


router = APIRouter(tags=["events-vote"])


@router.get(
    "/events/{event_id}/votes/me",
    response_model=VoteViewResponse
)
def get_user_vote(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
) -> VoteViewResponse:
    """
    본인 투표 내역 조회 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 조회 가능
    - 투표하지 않은 경우 404 에러 반환
    """
    return vote_service.get_user_vote(
        event_id=event_id,
        user_id=current_user.id
    )


@router.post(
    "/events/{event_id}/votes",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_or_update_vote(
    event_id: UUID,
    request: VoteCreateRequest,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
) -> VoteResponse:
    """
    투표 생성/업데이트 API (upsert 패턴)
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 투표 가능
    - 이미 투표한 경우 기존 투표를 삭제하고 새로 생성 (업데이트)
    - option_id: 선택된 선택지 ID (해당 이벤트의 선택지여야 함)
    - criterion_ids: 기준 ID 리스트 (순서대로, 0번째 = 1순위)
      - 모든 기준이 해당 이벤트의 기준이어야 함
      - 중복 불가
      - 빈 리스트 불가
    """
    return vote_service.create_or_update_vote(
        event_id=event_id,
        user_id=current_user.id,
        option_id=request.option_id,
        criterion_ids=request.criterion_ids
    )


@router.get(
    "/events/{event_id}/votes/result",
    response_model=VoteResultResponse
)
def get_vote_result(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
) -> VoteResultResponse:
    """
    투표 결과 조회 API
    - FINISHED 상태에서만 조회 가능
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 조회 가능
    - 옵션별 투표 수, 전체 인원, 투표 참여 인원
    - 1순위로 가장 많이 꼽힌 기준
    - 우선순위별 가중치 부여한 기준 (1위=3점, 2위=2점, 3위=1점)
    """
    return vote_service.get_vote_result(
        event_id=event_id,
        user_id=current_user.id
    )
