from uuid import UUID

from app.models.event import MembershipStatusType
from app.services.event.base import EventBaseService
from app.schemas.event import EventOverviewResponse, OptionInfo, AdminInfo
from app.exceptions import NotFoundError


class EventOverviewService(EventBaseService):
    """Event_Overview (3-1-0) 관련 서비스"""
    
    def get_event_overview(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> EventOverviewResponse:
        """
        이벤트 오버뷰 정보 조회
        - event, options, admin, participant_count, membership_status, can_enter 반환
        """
        # 이벤트 조회 (options, admin 조인)
        event = self.repos.event.get_event_with_relations(event_id)
        
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        # 참가 인원 수 카운트 (ACCEPTED만) - base 메서드 사용
        participant_count = self.count_accepted_members(event_id)
        
        # 현재 사용자의 멤버십 상태 조회
        membership_status = self.repos.event.get_membership_status(user_id, event_id)
        if membership_status is None:
            raise NotFoundError(
                message="Membership not found",
                detail=f"Membership with user_id {user_id} and event_id {event_id} not found"
            )
        
        # can_enter 결정 (ACCEPTED일 때만 true)
        can_enter = membership_status == MembershipStatusType.ACCEPTED if membership_status else False
        
        return EventOverviewResponse(
            event={
                "id": event.id,
                "decision_subject": event.decision_subject,
                "event_status": event.event_status,
                "entrance_code": event.entrance_code,
            },
            options=[
                OptionInfo(id=option.id, content=option.content)
                for option in event.options
            ],
            admin=AdminInfo(
                id=event.admin.id,
                name=event.admin.name,
                email=event.admin.email,
            ),
            participant_count=participant_count,
            membership_status=membership_status,
            can_enter=can_enter,
        )
