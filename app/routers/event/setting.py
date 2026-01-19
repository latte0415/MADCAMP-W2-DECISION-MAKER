from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends

from app.models import User
from app.services.event import EventService
from app.services.event.membership_service import MembershipService
from app.services.event.setting_service import EventSettingService
from app.schemas.event import (
    EventResponse,
    EventUpdateRequest,
    EventSettingResponse,
    EventStatusUpdateRequest,
    EventStatusUpdateResponse,
    MembershipResponse,
    BulkMembershipResponse,
    MembershipListItemResponse,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import (
    get_event_service,
    get_membership_service,
    get_setting_service,
)


router = APIRouter(tags=["events-setting"])


@router.get("/events/{event_id}/setting", response_model=EventSettingResponse)
def get_event_setting(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventSettingResponse:
    """
    이벤트 설정 편집용 정보 조회 API (관리자용)
    - 수정하기 위해 보여줘야 할 정보 반환
    - overview와 유사하지만 편집을 위한 모든 정보 포함
    """
    return event_service.get_event_setting(
        event_id=event_id,
        user_id=current_user.id
    )


@router.patch("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: UUID,
    request: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventResponse:
    """
    이벤트 설정 수정 API (관리자용)
    - 기본 정보 (except 최대 인원): NOT_STARTED인 경우만 수정 가능
    - 최대 인원: FINISHED가 아닐 때 수정 가능 (현재 인원보다 작을 수 없음)
    - 투표 허용 정책 + 입장 정책: FINISHED가 아닐 때 수정 가능
    """
    event = event_service.update_event(
        event_id=event_id,
        request=request,
        user_id=current_user.id
    )
    return EventResponse.model_validate(event)


@router.patch(
    "/events/{event_id}/memberships/{membership_id}/approve",
    response_model=MembershipResponse
)
def approve_membership(
    event_id: UUID,
    membership_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    """
    특정 참가자 참가 승인 API (관리자용)
    - membership_status를 PENDING에서 ACCEPTED로 변경
    - max_membership 초과 시 에러
    """
    membership = membership_service.approve_membership(
        event_id=event_id,
        membership_id=membership_id,
        user_id=current_user.id
    )
    return MembershipResponse(
        message="Membership approved successfully",
        membership_id=membership.id,
        membership_status=membership.membership_status,
    )


@router.patch(
    "/events/{event_id}/memberships/{membership_id}/reject",
    response_model=MembershipResponse
)
def reject_membership(
    event_id: UUID,
    membership_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    """
    특정 참가자 참가 거부 API (관리자용)
    - membership_status를 PENDING에서 REJECTED로 변경
    """
    membership = membership_service.reject_membership(
        event_id=event_id,
        membership_id=membership_id,
        user_id=current_user.id
    )
    return MembershipResponse(
        message="Membership rejected successfully",
        membership_id=membership.id,
        membership_status=membership.membership_status,
    )


@router.post(
    "/events/{event_id}/memberships/bulk-approve",
    response_model=BulkMembershipResponse
)
def bulk_approve_memberships(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
) -> BulkMembershipResponse:
    """
    신청한 참가자 전부 참가 승인 API (관리자용)
    - PENDING 상태인 모든 멤버십을 ACCEPTED로 변경
    - max_membership 초과 시 실패 처리
    """
    result = membership_service.bulk_approve_memberships(
        event_id=event_id,
        user_id=current_user.id
    )
    return BulkMembershipResponse(
        message="Bulk approval completed",
        approved_count=result["approved_count"],
        failed_count=result["failed_count"],
    )


@router.post(
    "/events/{event_id}/memberships/bulk-reject",
    response_model=BulkMembershipResponse
)
def bulk_reject_memberships(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
) -> BulkMembershipResponse:
    """
    신청한 참가자 전부 참가 거부 API (관리자용)
    - PENDING 상태인 모든 멤버십을 REJECTED로 변경
    """
    result = membership_service.bulk_reject_memberships(
        event_id=event_id,
        user_id=current_user.id
    )
    return BulkMembershipResponse(
        message="Bulk rejection completed",
        rejected_count=result["rejected_count"],
    )


@router.get(
    "/events/{event_id}/memberships",
    response_model=List[MembershipListItemResponse]
)
def get_event_memberships(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    event_service: EventService = Depends(get_event_service),
) -> List[MembershipListItemResponse]:
    """
    이벤트의 모든 멤버십 목록 조회 API (관리자용)
    - 현재 참가신청된 사용자 정보 (status와 무관하게 전부)
    - user_id, membership_id, status, 신청 일시(created_at), 승인 일시(joined_at), is_me, is_admin 반환
    """
    # 관리자 권한 확인을 위해 이벤트 조회 (admin_id 확인용)
    event = event_service.verify_admin(event_id, current_user.id)
    
    # 멤버십 목록 조회
    memberships = membership_service.get_event_memberships(
        event_id=event_id,
        user_id=current_user.id
    )
    
    return [
        MembershipListItemResponse(
            user_id=membership.user_id,
            membership_id=membership.id,
            status=membership.membership_status,
            created_at=membership.created_at,
            joined_at=membership.joined_at,
            is_me=membership.user_id == current_user.id,
            is_admin=membership.user_id == event.admin_id,
        )
        for membership in memberships
    ]


@router.patch(
    "/events/{event_id}/status",
    response_model=EventStatusUpdateResponse
)
def update_event_status(
    event_id: UUID,
    request: EventStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    setting_service: EventSettingService = Depends(get_setting_service),
) -> EventStatusUpdateResponse:
    """
    이벤트 상태 변경 API (관리자용)
    - 관리자 권한 필요
    - 상태 전이 규칙:
      - NOT_STARTED → IN_PROGRESS (시작)
      - IN_PROGRESS → PAUSED (일시정지)
      - PAUSED → IN_PROGRESS (재개)
      - IN_PROGRESS → FINISHED (종료)
      - PAUSED → FINISHED (종료)
    """
    return setting_service.update_event_status(
        event_id=event_id,
        new_status=request.status,
        user_id=current_user.id
    )
