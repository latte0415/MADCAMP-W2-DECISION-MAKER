from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import User
from app.services.event_service import EventService
from app.services.membership_service import MembershipService
from app.schemas.event import (
    EventCreateRequest,
    EventResponse,
    EntranceCodeCheckRequest,
    EntranceCodeCheckResponse,
    EntranceCodeGenerateResponse,
    EventListItemResponse,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_event_service, get_membership_service


router = APIRouter()


# ============================================================================
# Home (3-0-0) 관련 API
# ============================================================================

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


# ============================================================================
# Event_Creation (3-2-0) 관련 API
# ============================================================================

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


# ============================================================================
# Event_Overview (3-1-0) 관련 API
# ============================================================================

# TODO: POST /events/entry - 이벤트 입장 (코드로 참가 요청)


# ============================================================================
# Event (4-0-0) 관련 API
# ============================================================================

# TODO: GET /events/{event_id} - 이벤트 상세 조회
# TODO: POST /events/{event_id}/assumption-proposals - 전제 제안 생성
# TODO: POST /events/{event_id}/criteria-proposals - 기준 제안 생성
# TODO: POST /events/{event_id}/assumption-proposals/{proposal_id}/votes - 전제 제안 투표
# TODO: POST /events/{event_id}/criteria-proposals/{proposal_id}/votes - 기준 제안 투표
# TODO: POST /events/{event_id}/criteria/{criterion_id}/conclusion-proposals - 결론 제안 생성
# TODO: POST /events/{event_id}/conclusion-proposals/{proposal_id}/votes - 결론 제안 투표
# TODO: GET /events/{event_id}/criteria/{criterion_id}/comments - 코멘트 조회
# TODO: POST /events/{event_id}/criteria/{criterion_id}/comments - 코멘트 생성
# TODO: PATCH /events/{event_id}/comments/{comment_id} - 코멘트 수정
# TODO: DELETE /events/{event_id}/comments/{comment_id} - 코멘트 삭제


# ============================================================================
# Event_Setting (4-1-0) 관련 API
# ============================================================================

# TODO: PATCH /events/{event_id} - 이벤트 설정 수정


# ============================================================================
# Event_Vote (4-2-0) 관련 API
# ============================================================================

# TODO: GET /events/{event_id}/votes/me - 본인 투표 내역 조회
# TODO: POST /events/{event_id}/votes - 투표 생성/업데이트



