from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import EventMembership, MembershipStatusType
from app.repositories.membership_repository import MembershipRepository
from app.repositories.event_repository import EventRepository
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.services.event.base import EventBaseService
from app.exceptions import NotFoundError, ConflictError, ValidationError
from app.utils.transaction import transaction


# 멤버십 상태별 에러 메시지 상수
MEMBERSHIP_STATUS_ERROR_MESSAGES = {
    MembershipStatusType.ACCEPTED: "이미 가입되었습니다.",
    MembershipStatusType.PENDING: "이미 신청되었습니다. (승인 대기 중)",
    MembershipStatusType.REJECTED: "이미 가입 신청이 거절되었습니다.",
}


class MembershipService(EventBaseService):
    """Event Membership 관련 서비스"""
    
    def __init__(
        self,
        db: Session,
        repos: EventAggregateRepositories,
        membership_repo: MembershipRepository,
        event_repo: EventRepository
    ):
        super().__init__(db, repos)
        self.membership_repo = membership_repo
        self.event_repo = event_repo

    def create_admin_membership(self, event_id: UUID, admin_id: UUID) -> EventMembership:
        """
        이벤트 생성 시 관리자를 멤버십에 자동 추가
        - 관리자는 자동으로 ACCEPTED 상태
        - joined_at을 현재 시간으로 설정
        """
        membership = EventMembership(
            user_id=admin_id,
            event_id=event_id,
            membership_status=MembershipStatusType.ACCEPTED,
            joined_at=datetime.now(timezone.utc),
        )
        with transaction(self.db):
            result = self.membership_repo.create_membership(membership)
        return result

    def join_event_by_code(self, entrance_code: str, user_id: UUID) -> tuple[UUID, str]:
        """
        입장 코드로 이벤트 참가 신청
        - entrance_code로 이벤트 조회
        - 이미 멤버십이 있으면 ConflictError 발생
        - 없으면 PENDING 상태로 멤버십 생성
        - 반환: (event_id, message)
        """
        # 입장 코드로 이벤트 조회
        event = self.event_repo.get_by_entrance_code(entrance_code)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail="존재하지 않는 정보입니다."
            )
        
        # 현재 사용자의 멤버십 여부 조회
        existing_membership = self.membership_repo.get_by_user_and_event(user_id, event.id)
        
        if existing_membership:
            # 상태별 에러 메시지 (상수에서 조회)
            detail = MEMBERSHIP_STATUS_ERROR_MESSAGES.get(
                existing_membership.membership_status,
                "이미 신청되었습니다."
            )
            
            raise ConflictError(
                message="Already joined",
                detail=detail
            )
        
        # PENDING 상태로 멤버십 생성
        membership = EventMembership(
            user_id=user_id,
            event_id=event.id,
            membership_status=MembershipStatusType.PENDING,
            joined_at=None,  # ACCEPTED가 되면 설정됨
        )
        with transaction(self.db):
            self.membership_repo.create_membership(membership)
        return event.id, "정상적으로 신청되었습니다."


    def approve_membership(
        self,
        event_id: UUID,
        membership_id: UUID,
        user_id: UUID
    ) -> EventMembership:
        """멤버십 승인"""
        
        # 관리자 권한 확인 (base 메서드 사용)
        self.verify_admin(event_id, user_id)
        
        # 멤버십 조회 및 검증 (존재 여부, event_id 확인)
        membership = self._validate_membership_exists_and_belongs_to_event(
            membership_id, event_id
        )
        
        # max_membership 확인
        current_count = self.event_repo.count_accepted_members(event_id)
        event = self.event_repo.get_by_id(event_id)
        
        if event and current_count >= event.max_membership:
            raise ConflictError(
                message="Membership limit reached",
                detail=f"Event has reached maximum membership limit ({event.max_membership})"
            )
        
        # 조건부 UPDATE로 승인 처리 (원자성 보장)
        with transaction(self.db):
            joined_at = datetime.now(timezone.utc)
            updated_membership = self.membership_repo.approve_membership_if_pending(
                membership_id, joined_at
            )
            
            # 조건부 UPDATE 실패 (이미 처리됨)
            if updated_membership is None:
                # 현재 상태 확인
                self.db.refresh(membership)
                if membership.membership_status == MembershipStatusType.ACCEPTED:
                    raise ConflictError(
                        message="Membership already approved",
                        detail="This membership has already been approved"
                    )
                elif membership.membership_status == MembershipStatusType.REJECTED:
                    raise ConflictError(
                        message="Membership already rejected",
                        detail="This membership has already been rejected"
                    )
                else:
                    raise ConflictError(
                        message="Membership status changed",
                        detail="Membership status has changed and cannot be updated"
                    )
            
            result = updated_membership
        return result

    def reject_membership(
        self,
        event_id: UUID,
        membership_id: UUID,
        user_id: UUID
    ) -> EventMembership:
        """멤버십 거부"""
        
        # 관리자 권한 확인 (base 메서드 사용)
        self.verify_admin(event_id, user_id)
        
        # 멤버십 조회 및 검증 (존재 여부, event_id 확인)
        membership = self._validate_membership_exists_and_belongs_to_event(
            membership_id, event_id
        )
        
        # 조건부 UPDATE로 거부 처리 (원자성 보장)
        with transaction(self.db):
            updated_membership = self.membership_repo.reject_membership_if_pending(
                membership_id
            )
            
            # 조건부 UPDATE 실패 (이미 처리됨)
            if updated_membership is None:
                # 현재 상태 확인
                self.db.refresh(membership)
                if membership.membership_status == MembershipStatusType.ACCEPTED:
                    raise ConflictError(
                        message="Membership already approved",
                        detail="This membership has already been approved"
                    )
                elif membership.membership_status == MembershipStatusType.REJECTED:
                    raise ConflictError(
                        message="Membership already rejected",
                        detail="This membership has already been rejected"
                    )
                else:
                    raise ConflictError(
                        message="Membership status changed",
                        detail="Membership status has changed and cannot be updated"
                    )
            
            result = updated_membership
        return result

    def bulk_approve_memberships(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> dict:
        """멤버십 일괄 승인"""
        
        # 관리자 권한 확인 (base 메서드 사용)
        self.verify_admin(event_id, user_id)
        
        # PENDING 상태 멤버십 조회
        pending_memberships = self.membership_repo.get_pending_by_event_id(event_id)
        
        if not pending_memberships:
            return {
                "approved_count": 0,
                "failed_count": 0,
            }
        
        # max_membership 확인
        current_count = self.event_repo.count_accepted_members(event_id)
        event = self.event_repo.get_by_id(event_id)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        approved_count = 0
        failed_count = 0
        joined_at = datetime.now(timezone.utc)
        
        with transaction(self.db):
            for membership in pending_memberships:
                if current_count >= event.max_membership:
                    failed_count += 1
                    continue
                
                # 조건부 UPDATE로 승인 시도
                updated_membership = self.membership_repo.approve_membership_if_pending(
                    membership.id, joined_at
                )
                
                # 조건부 UPDATE 성공한 경우만 카운트
                if updated_membership is not None:
                    approved_count += 1
                    current_count += 1
                else:
                    # 이미 처리됨 (다른 요청에서 처리된 경우)
                    failed_count += 1
        
        return {
            "approved_count": approved_count,
            "failed_count": failed_count,
        }

    def bulk_reject_memberships(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> dict:
        """멤버십 일괄 거부"""
        # 관리자 권한 확인 (base 메서드 사용)
        self.verify_admin(event_id, user_id)
        
        # PENDING 상태 멤버십 조회
        pending_memberships = self.membership_repo.get_pending_by_event_id(event_id)
        
        if not pending_memberships:
            return {
                "rejected_count": 0,
            }
        
        rejected_count = 0
        
        with transaction(self.db):
            for membership in pending_memberships:
                # 조건부 UPDATE로 거부 시도
                updated_membership = self.membership_repo.reject_membership_if_pending(
                    membership.id
                )
                
                # 조건부 UPDATE 성공한 경우만 카운트
                if updated_membership is not None:
                    rejected_count += 1
        
        return {
            "rejected_count": rejected_count,
        }

    def _validate_membership_exists_and_belongs_to_event(
        self, membership_id: UUID, event_id: UUID
    ) -> EventMembership:
        """멤버십 존재 및 event_id 검증"""
        membership = self.membership_repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundError(
                message="Membership not found",
                detail=f"Membership with id {membership_id} not found"
            )
        if membership.event_id != event_id:
            raise NotFoundError(
                message="Membership not found",
                detail=f"Membership with id {membership_id} does not belong to this event"
            )
        return membership

    def _validate_membership_pending(
        self, membership: EventMembership, operation: str
    ) -> None:
        """멤버십 PENDING 상태 검증"""
        if membership.membership_status != MembershipStatusType.PENDING:
            raise ValidationError(
                message="Invalid membership status",
                detail=f"Membership status must be PENDING to {operation}, current status: {membership.membership_status.value}"
            )

    def get_event_memberships(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> List[EventMembership]:
        """
        이벤트의 모든 멤버십 목록 조회 (관리자용)
        - status와 무관하게 전부 반환
        """
        # 관리자 권한 확인 (base 메서드 사용)
        self.verify_admin(event_id, user_id)
        
        # 모든 멤버십 조회
        return self.membership_repo.get_all_by_event_id(event_id)
