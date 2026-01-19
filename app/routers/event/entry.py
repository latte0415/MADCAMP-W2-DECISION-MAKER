from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models import User
from app.services.event import EventService
from app.services.event.membership_service import MembershipService
from app.schemas.event import (
    EntranceCodeEntryRequest,
    EventEntryResponse,
    EventOverviewResponse,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import (
    get_event_service,
    get_membership_service,
)


router = APIRouter(tags=["events-entry"])


@router.post("/events/entry", response_model=EventEntryResponse, status_code=status.HTTP_201_CREATED)
def join_event_by_code(
    request: EntranceCodeEntryRequest,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
) -> EventEntryResponse:
    """
    이벤트 입장 API (코드로 참가 요청)
    - entrance_code로 이벤트 조회
    - 이미 멤버십이 있으면 에러
    - 없으면 PENDING 상태로 멤버십 생성
    """
    event_id, message = membership_service.join_event_by_code(
        entrance_code=request.entrance_code,
        user_id=current_user.id
    )
    return EventEntryResponse(
        message=message,
        event_id=event_id
    )


@router.get("/events/{event_id}/overview", response_model=EventOverviewResponse)
def get_event_overview(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventOverviewResponse:
    """
    이벤트 오버뷰 정보 조회 API
    - event, options, admin, participant_count, membership_status, can_enter 반환
    """
    return event_service.get_event_overview(
        event_id=event_id,
        user_id=current_user.id
    )
