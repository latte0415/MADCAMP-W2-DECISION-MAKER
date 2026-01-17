import random
import string
from uuid import UUID
from typing import List
from sqlalchemy.orm import Session

from app.models.event import Event, Option, EventStatusType
from app.models.content import Assumption, Criterion
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.schemas.event import (
    EventCreateRequest,
    OptionAttachRequest,
    AssumptionAttachRequest,
    CriterionAttachRequest,
    EventListItemResponse,
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
        raise ValueError("Failed to generate unique entrance code after 30 attempts")

    def get_events_participated(self, user_id: UUID) -> List[EventListItemResponse]:
        """사용자가 참가한 이벤트 목록 조회 (최적화 버전)"""
        events = self.repos.event.get_events_by_user_id(user_id)
        
        if not events:
            return []
        
        # 모든 이벤트 ID 수집
        event_ids = [event.id for event in events]
        
        # 한 번의 쿼리로 모든 참가 인원 수 조회
        participant_counts = self.repos.event.get_participant_counts_by_event_ids(event_ids)
        
        # 한 번의 쿼리로 모든 멤버십 상태 조회
        membership_statuses = self.repos.event.get_membership_statuses_by_event_ids(user_id, event_ids)
        
        # 기존 코드 (N+1 쿼리 문제)
        # result = []
        # for event in events:
        #     # 참가 인원 카운트 (ACCEPTED만)
        #     participant_count = self.repos.event.count_accepted_members(event.id)
        #     
        #     # 멤버십 상태 조회
        #     membership_status = self.repos.event.get_membership_status(user_id, event.id)
        #     
        #     # 관리자 여부 확인
        #     is_admin = event.admin_id == user_id
        #     
        #     # 관리자 이름 (email 사용, User 모델에 name이 없으므로)
        #     admin_name = event.admin.email if event.admin else None
        #     
        #     result.append(
        #         EventListItemResponse(
        #             id=event.id,
        #             decision_subject=event.decision_subject,
        #             event_status=event.event_status,
        #             admin_id=event.admin_id,
        #             admin_name=admin_name,
        #             entrance_code=event.entrance_code,
        #             participant_count=participant_count,
        #             is_admin=is_admin,
        #             membership_status=membership_status,
        #         )
        #     )
        # return result
        
        # 최적화 버전: 메모리에서 매핑
        result = []
        for event in events:
            # 참가 인원 카운트 (딕셔너리에서 조회, 없으면 0)
            participant_count = participant_counts.get(event.id, 0)
            
            # 멤버십 상태 (딕셔너리에서 조회, 없으면 None)
            membership_status = membership_statuses.get(event.id)
            
            # 관리자 여부 확인
            is_admin = event.admin_id == user_id
            
            # 관리자 이름 (email 사용, User 모델에 name이 없으므로)
            admin_name = event.admin.email if event.admin else None
            
            result.append(
                EventListItemResponse(
                    id=event.id,
                    decision_subject=event.decision_subject,
                    event_status=event.event_status,
                    admin_id=event.admin_id,
                    admin_name=admin_name,
                    entrance_code=event.entrance_code,
                    participant_count=participant_count,
                    is_admin=is_admin,
                    membership_status=membership_status,
                )
            )
        
        return result

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