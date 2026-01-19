from fastapi import APIRouter, Depends, status

from app.models import User
from app.services.event import EventService
from app.services.event.membership_service import MembershipService
from app.schemas.event import (
    EventCreateRequest,
    EventResponse,
    EntranceCodeCheckRequest,
    EntranceCodeCheckResponse,
    EntranceCodeGenerateResponse,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import (
    get_event_service,
    get_membership_service,
)


router = APIRouter(tags=["events-creation"])


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    request: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    membership_service: MembershipService = Depends(get_membership_service),
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
    
    # 5. 멤버십 생성
    membership_service.create_admin_membership(event.id, current_user.id)

    return EventResponse.model_validate(event)


@router.post("/events/entrance-code/check", response_model=EntranceCodeCheckResponse)
def check_entrance_code(
    request: EntranceCodeCheckRequest,
    event_service: EventService = Depends(get_event_service),
) -> EntranceCodeCheckResponse:
    """
    입장 코드 중복 확인 API
    - 중복이 없으면 is_available=True 반환
    """
    is_available = event_service.check_entrance_code_availability(request.entrance_code)
    return EntranceCodeCheckResponse(
        entrance_code=request.entrance_code,
        is_available=is_available,
    )


@router.get("/events/entrance-code/generate", response_model=EntranceCodeGenerateResponse)
def generate_entrance_code(
    event_service: EventService = Depends(get_event_service),
) -> EntranceCodeGenerateResponse:
    """
    랜덤 입장 코드 생성 API
    - 중복 검사 후 사용 가능한 코드 반환
    """
    code = event_service.get_random_code()
    return EntranceCodeGenerateResponse(code=code)
