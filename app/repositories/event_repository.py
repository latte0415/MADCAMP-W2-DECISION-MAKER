from typing import List, Dict
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.event import Event, EventMembership, MembershipStatusType
from app.exceptions import ConflictError, InternalError


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: Event) -> Event:
        """이벤트 생성"""
        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError(
                message="Event creation failed",
                detail=f"Failed to create event: {str(e)}"
            ) from e
        except OperationalError as e:
            self.db.rollback()
            raise InternalError(
                message="Database operation failed",
                detail="Failed to create event due to database error"
            ) from e

    def exists_by_entrance_code(self, entrance_code: str) -> bool:
        """입장 코드 중복 확인"""
        stmt = select(Event).where(Event.entrance_code == entrance_code)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

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
