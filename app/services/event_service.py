import random
import string
from uuid import UUID
from typing import List
from sqlalchemy.orm import Session

from app.models.event import Event, Option, EventStatusType, MembershipStatusType
from app.models.content import Assumption, Criterion
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.event import (
        EventUpdateRequest,
        OptionUpdateItem,
        AssumptionUpdateItem,
        CriterionUpdateItem,
    )
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.exceptions import InternalError, NotFoundError
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

    def get_event_overview(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> dict:
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
        
        # 참가 인원 수 카운트 (ACCEPTED만)
        participant_count = self.repos.event.count_accepted_members(event_id)
        
        # 현재 사용자의 멤버십 상태 조회
        membership_status = self.repos.event.get_membership_status(user_id, event_id)
        if membership_status is None:
            raise NotFoundError(
                message="Membership not found",
                detail=f"Membership with user_id {user_id} and event_id {event_id} not found"
            )
        
        # can_enter 결정 (ACCEPTED일 때만 true)
        can_enter = membership_status == MembershipStatusType.ACCEPTED if membership_status else False
        
        return {
            "event": {
                "id": event.id,
                "decision_subject": event.decision_subject,
                "event_status": event.event_status,
                "entrance_code": event.entrance_code,
            },
            "options": [
                {"id": option.id, "content": option.content}
                for option in event.options
            ],
            "admin": {
                "id": event.admin.id,
                "email": event.admin.email,
            },
            "participant_count": participant_count,
            "membership_status": membership_status,
            "can_enter": can_enter,
        }

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

    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        event = self.repos.event.get_by_id(event_id)
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        if event.admin_id != user_id:
            from app.exceptions import ForbiddenError
            raise ForbiddenError(
                message="Forbidden",
                detail="Only event administrator can perform this action"
            )
        
        return event

    def update_event(
        self,
        event_id: UUID,
        request: "EventUpdateRequest",
        user_id: UUID
    ) -> Event:
        """이벤트 정보 수정"""
        from app.exceptions import ValidationError
        
        # 관리자 권한 확인 및 이벤트 조회
        event = self.verify_admin(event_id, user_id)
        
        # 기본 정보 수정 (NOT_STARTED일 때만)
        if request.decision_subject is not None:
            if event.event_status != EventStatusType.NOT_STARTED:
                raise ValidationError(
                    message="Cannot modify decision subject",
                    detail="Decision subject can only be modified when event status is NOT_STARTED"
                )
            event.decision_subject = request.decision_subject
        
        # 선택지 업데이트 (NOT_STARTED일 때만)
        if request.options is not None:
            if event.event_status != EventStatusType.NOT_STARTED:
                raise ValidationError(
                    message="Cannot modify options",
                    detail="Options can only be modified when event status is NOT_STARTED"
                )
            self._update_options(event_id, request.options, user_id)
        
        # 전제 업데이트 (NOT_STARTED일 때만)
        if request.assumptions is not None:
            if event.event_status != EventStatusType.NOT_STARTED:
                raise ValidationError(
                    message="Cannot modify assumptions",
                    detail="Assumptions can only be modified when event status is NOT_STARTED"
                )
            self._update_assumptions(event_id, request.assumptions, user_id)
        
        # 기준 업데이트 (NOT_STARTED일 때만)
        if request.criteria is not None:
            if event.event_status != EventStatusType.NOT_STARTED:
                raise ValidationError(
                    message="Cannot modify criteria",
                    detail="Criteria can only be modified when event status is NOT_STARTED"
                )
            self._update_criteria(event_id, request.criteria, user_id)
        
        # 최대 인원 수정 (FINISHED가 아닐 때)
        if request.max_membership is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify max membership",
                    detail="Max membership cannot be modified when event status is FINISHED"
                )
            # 현재 ACCEPTED 멤버 수 확인
            current_count = self.repos.event.count_accepted_members(event_id)
            if request.max_membership < current_count:
                raise ValidationError(
                    message="Invalid max membership",
                    detail=f"Max membership ({request.max_membership}) cannot be less than current participant count ({current_count})"
                )
            event.max_membership = request.max_membership
        
        # 투표 허용 정책 수정 (FINISHED가 아닐 때)
        if request.assumption_is_auto_approved_by_votes is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify assumption auto approval policy",
                    detail="Voting policies cannot be modified when event status is FINISHED"
                )
            event.assumption_is_auto_approved_by_votes = request.assumption_is_auto_approved_by_votes
        
        if request.assumption_min_votes_required is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify assumption min votes required",
                    detail="Voting policies cannot be modified when event status is FINISHED"
                )
            event.assumption_min_votes_required = request.assumption_min_votes_required
        
        if request.criteria_is_auto_approved_by_votes is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify criteria auto approval policy",
                    detail="Voting policies cannot be modified when event status is FINISHED"
                )
            event.criteria_is_auto_approved_by_votes = request.criteria_is_auto_approved_by_votes
        
        if request.criteria_min_votes_required is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify criteria min votes required",
                    detail="Voting policies cannot be modified when event status is FINISHED"
                )
            event.criteria_min_votes_required = request.criteria_min_votes_required
        
        if request.conclusion_approval_threshold_percent is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify conclusion approval threshold",
                    detail="Voting policies cannot be modified when event status is FINISHED"
                )
            event.conclusion_approval_threshold_percent = request.conclusion_approval_threshold_percent
        
        # 입장 정책 수정 (FINISHED가 아닐 때)
        if request.membership_is_auto_approved is not None:
            if event.event_status == EventStatusType.FINISHED:
                raise ValidationError(
                    message="Cannot modify membership auto approval policy",
                    detail="Entrance policies cannot be modified when event status is FINISHED"
                )
            event.membership_is_auto_approved = request.membership_is_auto_approved
        
        # 이벤트 업데이트
        result = self.repos.event.update_event(event)
        self.db.commit()
        return result

    def _update_options(
        self,
        event_id: UUID,
        option_items: List["OptionUpdateItem"],
        user_id: UUID
    ) -> None:
        """선택지 업데이트 처리"""
        from app.exceptions import NotFoundError
        
        for item in option_items:
            if item.id is None:
                # 추가
                if item.content:
                    option = Option(
                        event_id=event_id,
                        content=item.content,
                        created_by=user_id,
                    )
                    self.repos.option.create_options([option])
            elif item.content is None:
                # 삭제 (content가 None)
                option = self.repos.option.get_by_id(item.id)
                if not option or option.event_id != event_id:
                    raise NotFoundError(
                        message="Option not found",
                        detail=f"Option with id {item.id} not found for this event"
                    )
                self.repos.option.delete_option(option)
            else:
                # 수정
                option = self.repos.option.get_by_id(item.id)
                if not option or option.event_id != event_id:
                    raise NotFoundError(
                        message="Option not found",
                        detail=f"Option with id {item.id} not found for this event"
                    )
                option.content = item.content
                self.repos.option.update_option(option)

    def _update_assumptions(
        self,
        event_id: UUID,
        assumption_items: List["AssumptionUpdateItem"],
        user_id: UUID
    ) -> None:
        """전제 업데이트 처리"""
        from app.exceptions import NotFoundError
        
        for item in assumption_items:
            if item.id is None:
                # 추가
                if item.content:
                    assumption = Assumption(
                        event_id=event_id,
                        content=item.content,
                        created_by=user_id,
                    )
                    self.repos.assumption.create_assumptions([assumption])
            elif item.content is None:
                # 삭제 (content가 None)
                assumption = self.repos.assumption.get_by_id(item.id)
                if not assumption or assumption.event_id != event_id:
                    raise NotFoundError(
                        message="Assumption not found",
                        detail=f"Assumption with id {item.id} not found for this event"
                    )
                self.repos.assumption.delete_assumption(assumption)
            else:
                # 수정
                assumption = self.repos.assumption.get_by_id(item.id)
                if not assumption or assumption.event_id != event_id:
                    raise NotFoundError(
                        message="Assumption not found",
                        detail=f"Assumption with id {item.id} not found for this event"
                    )
                assumption.content = item.content
                self.repos.assumption.update_assumption(assumption, user_id)

    def _update_criteria(
        self,
        event_id: UUID,
        criterion_items: List["CriterionUpdateItem"],
        user_id: UUID
    ) -> None:
        """기준 업데이트 처리"""
        from app.exceptions import NotFoundError
        
        for item in criterion_items:
            if item.id is None:
                # 추가
                if item.content:
                    criterion = Criterion(
                        event_id=event_id,
                        content=item.content,
                        created_by=user_id,
                    )
                    self.repos.criterion.create_criteria([criterion])
            elif item.content is None:
                # 삭제 (content가 None)
                criterion = self.repos.criterion.get_by_id(item.id)
                if not criterion or criterion.event_id != event_id:
                    raise NotFoundError(
                        message="Criterion not found",
                        detail=f"Criterion with id {item.id} not found for this event"
                    )
                self.repos.criterion.delete_criterion(criterion)
            else:
                # 수정
                criterion = self.repos.criterion.get_by_id(item.id)
                if not criterion or criterion.event_id != event_id:
                    raise NotFoundError(
                        message="Criterion not found",
                        detail=f"Criterion with id {item.id} not found for this event"
                    )
                criterion.content = item.content
                self.repos.criterion.update_criterion(criterion, user_id)

    def get_event_setting(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> dict:
        """
        이벤트 설정 편집용 정보 조회
        - 관리자 권한 확인 후 설정 정보 반환
        """
        # 관리자 권한 확인 및 이벤트 조회
        event = self.verify_admin(event_id, user_id)
        
        # 모든 관련 데이터 조인하여 조회
        event_with_all = self.repos.event.get_event_with_all_relations(event_id)
        
        if not event_with_all:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        return {
            "decision_subject": event_with_all.decision_subject,
            "options": [
                {"id": option.id, "content": option.content}
                for option in event_with_all.options
            ],
            "assumptions": [
                {"id": assumption.id, "content": assumption.content}
                for assumption in event_with_all.assumptions
            ],
            "criteria": [
                {"id": criterion.id, "content": criterion.content}
                for criterion in event_with_all.criteria
            ],
            "max_membership": event_with_all.max_membership,
            "assumption_is_auto_approved_by_votes": event_with_all.assumption_is_auto_approved_by_votes,
            "assumption_min_votes_required": event_with_all.assumption_min_votes_required,
            "criteria_is_auto_approved_by_votes": event_with_all.criteria_is_auto_approved_by_votes,
            "criteria_min_votes_required": event_with_all.criteria_min_votes_required,
            "conclusion_approval_threshold_percent": event_with_all.conclusion_approval_threshold_percent,
            "membership_is_auto_approved": event_with_all.membership_is_auto_approved,
            "entrance_code": event_with_all.entrance_code,
        }