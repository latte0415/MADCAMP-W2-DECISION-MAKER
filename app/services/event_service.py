from uuid import UUID
from typing import List
from sqlalchemy.orm import Session

from app.models.event import Event, Option
from app.models.content import Assumption, Criterion
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.schemas.event import (
    EventCreateRequest,
    OptionAttachRequest,
    AssumptionAttachRequest,
    CriterionAttachRequest,
)


class EventService:
    def __init__(
        self,
        db: Session,
        repos: EventAggregateRepositories,
    ):
        self.db = db
        self.repos = repos

    def create_event(
        self,
        request: EventCreateRequest,
        admin_id: UUID
    ) -> Event:
        """이벤트 생성"""
        event = self._create_event_from_request(request, admin_id)
        return self.repos.event.create_event(event)

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
        return self.repos.option.create_options(options)

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
        return self.repos.assumption.create_assumptions(assumptions)

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
        return self.repos.criterion.create_criteria(criteria)

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
            event_status=request.event_status,
            max_membership=request.max_membership,
            admin_id=admin_id,
        )