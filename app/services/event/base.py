from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Event
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.exceptions import NotFoundError, ForbiddenError


class EventBaseService:
    """Event 관련 공통 서비스 로직"""
    
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        self.db = db
        self.repos = repos
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        event = self.repos.event.get_by_id(event_id)
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
        
        return event
    
    def get_event_with_all_relations(self, event_id: UUID) -> Event:
        """이벤트 전체 조회 (모든 관계 포함)"""
        event = self.repos.event.get_event_with_all_relations(event_id)
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        return event
    
    def count_accepted_members(self, event_id: UUID) -> int:
        """참가 인원 카운트"""
        return self.repos.event.count_accepted_members(event_id)
