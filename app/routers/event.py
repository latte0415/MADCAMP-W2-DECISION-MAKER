from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import User
from app.services.event_service import EventService
from app.schemas.event import EventCreateRequest, EventResponse
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_event_service


router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    request: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventResponse:
    """
    이벤트 생성 API
    - event, options, assumptions, criteria를 한 번에 생성
    """
    # 1. 이벤트 생성
    event = event_service.create_event(request, admin_id=current_user.id)
    
    # 2. 선택지들 연결
    if request.options:
        event_service.attach_options(event.id, request.options, created_by=current_user.id)
    
    # 3. 전제들 연결
    if request.assumptions:
        event_service.attach_assumptions(event.id, request.assumptions, created_by=current_user.id)
    
    # 4. 기준들 연결
    if request.criteria:
        event_service.attach_criteria(event.id, request.criteria, created_by=current_user.id)
    
    return EventResponse.model_validate(event)
