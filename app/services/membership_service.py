from typing import List
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.event import EventMembership, MembershipStatusType
from app.repositories.membership_repository import MembershipRepository
from app.exceptions import NotFoundError, ConflictError, InternalError


class MembershipService:
    def __init__(self, db: Session, membership_repo: MembershipRepository):
        self.db = db
        self.membership_repo = membership_repo

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
        return self.membership_repo.create_membership(membership)

    def join_event_by_code(self, entrance_code: str, user_id: UUID) -> tuple[UUID, str]:
        """
        입장 코드로 이벤트 참가 신청
        - entrance_code로 이벤트 조회
        - 이미 멤버십이 있으면 ConflictError 발생
        - 없으면 PENDING 상태로 멤버십 생성
        - 반환: (event_id, message)
        """
        from app.repositories.event_repository import EventRepository
        
        # 입장 코드로 이벤트 조회
        event_repo = EventRepository(self.db)
        event = event_repo.get_by_entrance_code(entrance_code)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail="존재하지 않는 정보입니다."
            )
        
        # 현재 사용자의 멤버십 여부 조회
        existing_membership = self.membership_repo.get_by_user_and_event(user_id, event.id)
        
        if existing_membership:
            # 상태별 에러 메시지
            if existing_membership.membership_status == MembershipStatusType.ACCEPTED:
                detail = "이미 가입되었습니다."
            elif existing_membership.membership_status == MembershipStatusType.PENDING:
                detail = "이미 신청되었습니다. (승인 대기 중)"
            elif existing_membership.membership_status == MembershipStatusType.REJECTED:
                detail = "이미 가입 신청이 거절되었습니다."
            else:
                detail = "이미 신청되었습니다."
            
            raise ConflictError(
                message="Already joined",
                detail=detail
            )
        
        # PENDING 상태로 멤버십 생성
        try:
            membership = EventMembership(
                user_id=user_id,
                event_id=event.id,
                membership_status=MembershipStatusType.PENDING,
                joined_at=None,  # ACCEPTED가 되면 설정됨
            )
            self.membership_repo.create_membership(membership)
            return event.id, "정상적으로 신청되었습니다."
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError(
                message="Membership creation failed",
                detail=f"Failed to join event: {str(e)}"
            ) from e
        except OperationalError as e:
            self.db.rollback()
            raise InternalError(
                message="Database operation failed",
                detail="Failed to join event due to database error"
            ) from e

    def verify_admin(self, event_id: UUID, user_id: UUID) -> None:
        """이벤트 관리자 권한 확인"""
        from app.repositories.event_repository import EventRepository
        from app.exceptions import ForbiddenError, NotFoundError
        
        event_repo = EventRepository(self.db)
        event = event_repo.get_by_id(event_id)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        if event.admin_id != user_id:
            raise ForbiddenError(
                message="Forbidden",
                detail="Only event administrator can perform this action"
            )

    def approve_membership(
        self,
        event_id: UUID,
        membership_id: UUID,
        user_id: UUID
    ) -> EventMembership:
        """멤버십 승인"""
        from app.repositories.event_repository import EventRepository
        from app.exceptions import ValidationError, ConflictError
        
        # 관리자 권한 확인
        self.verify_admin(event_id, user_id)
        
        # 멤버십 조회
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
        
        if membership.membership_status != MembershipStatusType.PENDING:
            raise ValidationError(
                message="Invalid membership status",
                detail=f"Membership status must be PENDING to approve, current status: {membership.membership_status.value}"
            )
        
        # max_membership 확인
        event_repo = EventRepository(self.db)
        current_count = event_repo.count_accepted_members(event_id)
        event = event_repo.get_by_id(event_id)
        
        if event and current_count >= event.max_membership:
            raise ConflictError(
                message="Membership limit reached",
                detail=f"Event has reached maximum membership limit ({event.max_membership})"
            )
        
        # 승인 처리
        membership.membership_status = MembershipStatusType.ACCEPTED
        membership.joined_at = datetime.now(timezone.utc)
        
        return self.membership_repo.update_membership(membership)

    def reject_membership(
        self,
        event_id: UUID,
        membership_id: UUID,
        user_id: UUID
    ) -> EventMembership:
        """멤버십 거부"""
        from app.exceptions import ValidationError
        
        # 관리자 권한 확인
        self.verify_admin(event_id, user_id)
        
        # 멤버십 조회
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
        
        if membership.membership_status != MembershipStatusType.PENDING:
            raise ValidationError(
                message="Invalid membership status",
                detail=f"Membership status must be PENDING to reject, current status: {membership.membership_status.value}"
            )
        
        # 거부 처리
        membership.membership_status = MembershipStatusType.REJECTED
        
        return self.membership_repo.update_membership(membership)

    def bulk_approve_memberships(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> dict:
        """멤버십 일괄 승인"""
        from app.repositories.event_repository import EventRepository
        from app.exceptions import ConflictError
        
        # 관리자 권한 확인
        self.verify_admin(event_id, user_id)
        
        # PENDING 상태 멤버십 조회
        pending_memberships = self.membership_repo.get_pending_by_event_id(event_id)
        
        if not pending_memberships:
            return {
                "approved_count": 0,
                "failed_count": 0,
            }
        
        # max_membership 확인
        event_repo = EventRepository(self.db)
        current_count = event_repo.count_accepted_members(event_id)
        event = event_repo.get_by_id(event_id)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        approved_count = 0
        failed_count = 0
        
        for membership in pending_memberships:
            if current_count >= event.max_membership:
                failed_count += 1
                continue
            
            membership.membership_status = MembershipStatusType.ACCEPTED
            membership.joined_at = datetime.now(timezone.utc)
            self.membership_repo.update_membership(membership)
            approved_count += 1
            current_count += 1
        
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
        # 관리자 권한 확인
        self.verify_admin(event_id, user_id)
        
        # PENDING 상태 멤버십 조회
        pending_memberships = self.membership_repo.get_pending_by_event_id(event_id)
        
        if not pending_memberships:
            return {
                "rejected_count": 0,
            }
        
        rejected_count = 0
        
        for membership in pending_memberships:
            membership.membership_status = MembershipStatusType.REJECTED
            self.membership_repo.update_membership(membership)
            rejected_count += 1
        
        return {
            "rejected_count": rejected_count,
        }

    def get_event_memberships(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> List[EventMembership]:
        """
        이벤트의 모든 멤버십 목록 조회 (관리자용)
        - status와 무관하게 전부 반환
        """
        # 관리자 권한 확인
        self.verify_admin(event_id, user_id)
        
        # 모든 멤버십 조회
        return self.membership_repo.get_all_by_event_id(event_id)
