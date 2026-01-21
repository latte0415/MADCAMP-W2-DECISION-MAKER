from typing import List
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import update

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
        from sqlalchemy.orm import joinedload
        stmt = (
            select(EventMembership)
            .where(EventMembership.event_id == event_id)
            .options(joinedload(EventMembership.user))
            .order_by(EventMembership.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.unique().scalars().all())

    def approve_membership_if_pending(
        self, membership_id: UUID, joined_at: datetime
    ) -> EventMembership | None:
        """
        PENDING 상태인 멤버십을 조건부로 승인
        - WHERE id = :id AND status = 'PENDING' 조건으로 업데이트
        - 이미 승인/거절된 경우 None 반환 (중복 승인 방지)
        - 성공 시 업데이트된 membership 반환
        """
        stmt = (
            update(EventMembership)
            .where(
                EventMembership.id == membership_id,
                EventMembership.membership_status == MembershipStatusType.PENDING
            )
            .values(
                membership_status=MembershipStatusType.ACCEPTED,
                joined_at=joined_at
            )
            .returning(EventMembership)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()

    def reject_membership_if_pending(
        self, membership_id: UUID
    ) -> EventMembership | None:
        """
        PENDING 상태인 멤버십을 조건부로 거절
        - WHERE id = :id AND status = 'PENDING' 조건으로 업데이트
        - 이미 승인/거절된 경우 None 반환 (중복 거절 방지)
        - 성공 시 업데이트된 membership 반환
        """
        stmt = (
            update(EventMembership)
            .where(
                EventMembership.id == membership_id,
                EventMembership.membership_status == MembershipStatusType.PENDING
            )
            .values(
                membership_status=MembershipStatusType.REJECTED
            )
            .returning(EventMembership)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()
