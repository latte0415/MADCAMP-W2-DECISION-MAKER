from typing import List
from fastapi import APIRouter, Depends

from app.models import User
from app.services.event import EventService
from app.schemas.event import EventListItemResponse
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_event_service


router = APIRouter(tags=["events-home"])


@router.get("/events/participated", response_model=List[EventListItemResponse])
def get_events_participated(
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> List[EventListItemResponse]:
    """
    사용자가 참가한 이벤트 목록 조회 API
    - event_membership에서 조인해서 속한 event만 반환
    - 참가 인원, 관리자 정보, 멤버십 상태 포함
    """
    return event_service.get_events_participated(current_user.id)
