from typing import List
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
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
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

    def get_by_id(self, membership_id: UUID) -> EventMembership | None:
        """멤버십 ID로 조회"""
        from sqlalchemy import select
        stmt = select(EventMembership).where(EventMembership.id == membership_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_membership(self, membership: EventMembership) -> EventMembership:
        """멤버십 업데이트"""
        from datetime import datetime, timezone
        membership.updated_at = datetime.now(timezone.utc)
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(membership)
        return membership

    def get_pending_by_event_id(self, event_id: UUID) -> List[EventMembership]:
        """이벤트의 PENDING 상태 멤버십 목록 조회"""
        from sqlalchemy import select
        stmt = select(EventMembership).where(
            EventMembership.event_id == event_id,
            EventMembership.membership_status == MembershipStatusType.PENDING
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_all_by_event_id(self, event_id: UUID) -> List[EventMembership]:
        """이벤트의 모든 멤버십 목록 조회 (status와 무관하게 전부)"""
        from sqlalchemy import select
        stmt = select(EventMembership).where(
            EventMembership.event_id == event_id
        ).order_by(EventMembership.created_at.desc())
        result = self.db.execute(stmt)
        return list(result.scalars().all())
