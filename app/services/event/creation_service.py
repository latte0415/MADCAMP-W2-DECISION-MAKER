import random
import string
from uuid import UUID
from typing import List

from app.models.event import Event, Option, EventStatusType
from app.models.content import Assumption, Criterion
from app.services.event.base import EventBaseService
from app.schemas.event import (
    EventCreateRequest,
    OptionAttachRequest,
    AssumptionAttachRequest,
    CriterionAttachRequest,
)
from app.exceptions import InternalError


class EventCreationService(EventBaseService):
    """Event_Creation (3-2-0) 관련 서비스"""
    
    def create_event(
        self,
        request: EventCreateRequest,
        admin_id: UUID
    ) -> Event:
        """이벤트 생성"""
        event = self._create_event_from_request(request, admin_id)
        result = self.repos.event.create_event(event)
        self.db.commit()
        return result

    def attach_options(
        self,
        event_id: UUID,
        option_requests: List[OptionAttachRequest],
        created_by: UUID
    ) -> List[Option]:
        """선택지들을 이벤트에 연결"""
        options = [
            Option(
                event_id=event_id,
                content=req.content,
                created_by=created_by,
            )
            for req in option_requests
        ]
        result = self.repos.option.create_options(options)
        self.db.commit()
        return result

    def attach_assumptions(
        self,
        event_id: UUID,
        assumption_requests: List[AssumptionAttachRequest],
        created_by: UUID
    ) -> List[Assumption]:
        """전제들을 이벤트에 연결"""
        assumptions = [
            Assumption(
                event_id=event_id,
                content=req.content,
                created_by=created_by,
            )
            for req in assumption_requests
        ]
        result = self.repos.assumption.create_assumptions(assumptions)
        self.db.commit()
        return result

    def attach_criteria(
        self,
        event_id: UUID,
        criterion_requests: List[CriterionAttachRequest],
        created_by: UUID
    ) -> List[Criterion]:
        """기준들을 이벤트에 연결"""
        criteria = [
            Criterion(
                event_id=event_id,
                content=req.content,
                created_by=created_by,
            )
            for req in criterion_requests
        ]
        result = self.repos.criterion.create_criteria(criteria)
        self.db.commit()
        return result

    def check_entrance_code_availability(self, entrance_code: str) -> bool:
        """입장 코드 사용 가능 여부 확인 (중복이 없으면 True)"""
        return not self.repos.event.exists_by_entrance_code(entrance_code)

    def get_random_code(self) -> str:
        """
        랜덤 코드 생성 (중복 검사 포함)
        최대 30회 시도하여 중복이 없는 코드를 반환
        """
        MAX_ATTEMPTS = 30
        for _ in range(MAX_ATTEMPTS):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not self.repos.event.exists_by_entrance_code(code):
                return code
        
        # 30회 시도 후에도 중복이면 예외 발생 (매우 드문 경우)
        raise InternalError(
            message="Failed to generate unique entrance code",
            detail="Could not generate a unique entrance code after 30 attempts. Please try again."
        )

    def _create_event_from_request(
        self,
        request: EventCreateRequest,
        admin_id: UUID
    ) -> Event:
        """Event 모델 객체를 request로부터 생성"""
        return Event(
            decision_subject=request.decision_subject,
            entrance_code=request.entrance_code,
            assumption_is_auto_approved_by_votes=request.assumption_is_auto_approved_by_votes,
            criteria_is_auto_approved_by_votes=request.criteria_is_auto_approved_by_votes,
            membership_is_auto_approved=request.membership_is_auto_approved,
            conclusion_is_auto_approved_by_votes=request.conclusion_is_auto_approved_by_votes,
            assumption_min_votes_required=request.assumption_min_votes_required,
            criteria_min_votes_required=request.criteria_min_votes_required,
            conclusion_approval_threshold_percent=request.conclusion_approval_threshold_percent,
            event_status=EventStatusType.NOT_STARTED,
            max_membership=request.max_membership,
            admin_id=admin_id,
        )
