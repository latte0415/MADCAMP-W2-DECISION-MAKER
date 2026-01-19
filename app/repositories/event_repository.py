from typing import List, Dict
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.models.event import Event, EventMembership, MembershipStatusType


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: Event) -> Event:
        """이벤트 생성"""
        self.db.add(event)
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
        self.db.refresh(event)
        return event

    def exists_by_entrance_code(self, entrance_code: str) -> bool:
        """입장 코드 중복 확인"""
        stmt = select(Event).where(Event.entrance_code == entrance_code)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def get_by_entrance_code(self, entrance_code: str) -> Event | None:
        """입장 코드로 이벤트 조회"""
        stmt = select(Event).where(Event.entrance_code == entrance_code.upper())
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_event_with_relations(self, event_id: UUID) -> Event | None:
        """이벤트 조회 (options, admin 조인)"""
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                joinedload(Event.options),
                joinedload(Event.admin)
            )
        )
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_event_with_all_relations(self, event_id: UUID) -> Event | None:
        """이벤트 조회 (options, assumptions, criteria, admin 모두 조인)"""
        from app.models.content import Assumption, Criterion
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                joinedload(Event.options),
                joinedload(Event.assumptions),
                joinedload(Event.criteria),
                joinedload(Event.admin)
            )
        )
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_events_by_user_id(self, user_id: UUID) -> List[Event]:
        """사용자가 참가한 이벤트 목록 조회 (membership이 있는 이벤트)"""
        stmt = (
            select(Event)
            .join(EventMembership, Event.id == EventMembership.event_id)
            .where(EventMembership.user_id == user_id)
            .options(joinedload(Event.admin))
            .distinct()
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def count_accepted_members(self, event_id: UUID) -> int:
        """이벤트의 ACCEPTED 멤버 수 카운트"""
        stmt = (
            select(func.count(EventMembership.id))
            .where(
                EventMembership.event_id == event_id,
                EventMembership.membership_status == MembershipStatusType.ACCEPTED
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one() or 0

    def get_membership_status(self, user_id: UUID, event_id: UUID) -> MembershipStatusType | None:
        """사용자의 특정 이벤트 멤버십 상태 조회"""
        stmt = select(EventMembership).where(
            EventMembership.user_id == user_id,
            EventMembership.event_id == event_id
        )
        result = self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        return membership.membership_status if membership else None

    def get_participant_counts_by_event_ids(self, event_ids: List[UUID]) -> Dict[UUID, int]:
        """여러 이벤트의 ACCEPTED 멤버 수를 한 번에 조회"""
        if not event_ids:
            return {}
        
        stmt = (
            select(
                EventMembership.event_id,
                func.count(EventMembership.id).label('count')
            )
            .where(
                EventMembership.event_id.in_(event_ids),
                EventMembership.membership_status == MembershipStatusType.ACCEPTED
            )
            .group_by(EventMembership.event_id)
        )
        result = self.db.execute(stmt)
        return {row.event_id: row.count for row in result.all()}

    def get_membership_statuses_by_event_ids(
        self, 
        user_id: UUID, 
        event_ids: List[UUID]
    ) -> Dict[UUID, MembershipStatusType]:
        """사용자의 여러 이벤트 멤버십 상태를 한 번에 조회"""
        if not event_ids:
            return {}
        
        stmt = select(EventMembership).where(
            EventMembership.user_id == user_id,
            EventMembership.event_id.in_(event_ids)
        )
        result = self.db.execute(stmt)
        return {
            membership.event_id: membership.membership_status 
            for membership in result.scalars().all()
        }

    def get_by_id(self, event_id: UUID) -> Event | None:
        """이벤트 ID로 조회"""
        stmt = select(Event).where(Event.id == event_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_event(self, event: Event) -> Event:
        """이벤트 업데이트"""
        from datetime import datetime, timezone
        event.updated_at = datetime.now(timezone.utc)
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(event)
        return event
