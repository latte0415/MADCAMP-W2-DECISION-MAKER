from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event, EventStatusType, MembershipStatusType
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.exceptions import NotFoundError, ForbiddenError, ValidationError


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
    
    def _validate_event_status(
        self, event: Event, required_status: EventStatusType, operation: str
    ) -> None:
        """이벤트 상태 검증"""
        if event.event_status != required_status:
            raise ValidationError(
                message=f"Event not {required_status.value.lower().replace('_', ' ')}",
                detail=f"{operation} can only be performed when event status is {required_status.value}"
            )
    
    def _validate_membership_accepted(
        self, user_id: UUID, event_id: UUID, operation: str
    ) -> None:
        """멤버십 ACCEPTED 상태 검증"""
        membership_status = self.repos.event.get_membership_status(user_id, event_id)
        if membership_status != MembershipStatusType.ACCEPTED:
            raise ForbiddenError(
                message="Forbidden",
                detail=f"Only accepted members can {operation}"
            )
    
    def _validate_event_in_progress(self, event_id: UUID, operation: str) -> Event:
        """이벤트가 IN_PROGRESS 상태인지 검증하고 Event 반환"""
        event = self.get_event_with_all_relations(event_id)
        if event.event_status != EventStatusType.IN_PROGRESS:
            raise ValidationError(
                message="Event not in progress",
                detail=f"{operation} can only be performed when event status is IN_PROGRESS"
            )
        return event
    
    def _validate_event_not_started(self, event: Event, operation: str) -> None:
        """이벤트가 NOT_STARTED 상태인지 검증"""
        if event.event_status != EventStatusType.NOT_STARTED:
            raise ValidationError(
                message=f"Cannot {operation}",
                detail=f"{operation} can only be performed when event status is NOT_STARTED"
            )
    
    def _validate_event_not_finished(self, event: Event, operation: str) -> None:
        """이벤트가 FINISHED 상태가 아닌지 검증"""
        if event.event_status == EventStatusType.FINISHED:
            raise ValidationError(
                message=f"Cannot {operation}",
                detail=f"{operation} cannot be performed when event status is FINISHED"
            )