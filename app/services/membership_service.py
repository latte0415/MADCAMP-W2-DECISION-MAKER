from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import EventMembership, MembershipStatusType
from app.repositories.membership_repository import MembershipRepository


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
