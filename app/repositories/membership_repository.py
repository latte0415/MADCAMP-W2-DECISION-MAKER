from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import EventMembership, MembershipStatusType


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_membership(self, membership: EventMembership) -> EventMembership:
        """멤버십 생성"""
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def get_by_user_and_event(self, user_id: UUID, event_id: UUID) -> EventMembership | None:
        """사용자와 이벤트로 멤버십 조회"""
        from sqlalchemy import select
        stmt = select(EventMembership).where(
            EventMembership.user_id == user_id,
            EventMembership.event_id == event_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
