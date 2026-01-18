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
