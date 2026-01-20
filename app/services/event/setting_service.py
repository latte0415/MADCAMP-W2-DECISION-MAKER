from typing import List, TYPE_CHECKING
from uuid import UUID

from datetime import datetime, timezone

from app.models.event import Event, EventStatusType, Option
from app.models.content import Assumption, Criterion
from app.services.event.base import EventBaseService
from app.schemas.event import (
    EventSettingResponse,
    EventUpdateRequest,
    EventResponse,
    EventStatusUpdateResponse,
    OptionInfo,
    AssumptionInfo,
    CriterionInfo,
)
from app.exceptions import NotFoundError, ValidationError
from app.utils.transaction import transaction

if TYPE_CHECKING:
    from app.schemas.event import (
        OptionUpdateItem,
        AssumptionUpdateItem,
        CriterionUpdateItem,
    )


class EventSettingService(EventBaseService):
    """Event_Setting (4-1-0) 관련 서비스"""
    
    def get_event_setting(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> EventSettingResponse:
        """
        이벤트 설정 편집용 정보 조회
        - 관리자 권한 확인 후 설정 정보 반환
        """
        # 관리자 권한 확인 및 이벤트 조회 - base 메서드 사용
        event = self.verify_admin(event_id, user_id)
        
        # 모든 관련 데이터 조인하여 조회 - base 메서드 사용
        event_with_all = self.get_event_with_all_relations(event_id)
        
        return EventSettingResponse(
            decision_subject=event_with_all.decision_subject,
            options=[
                OptionInfo(id=option.id, content=option.content)
                for option in event_with_all.options
            ],
            assumptions=[
                AssumptionInfo(id=assumption.id, content=assumption.content)
                for assumption in event_with_all.assumptions
            ],
            criteria=[
                CriterionInfo(id=criterion.id, content=criterion.content)
                for criterion in event_with_all.criteria
            ],
            max_membership=event_with_all.max_membership,
            assumption_is_auto_approved_by_votes=event_with_all.assumption_is_auto_approved_by_votes,
            assumption_min_votes_required=event_with_all.assumption_min_votes_required,
            criteria_is_auto_approved_by_votes=event_with_all.criteria_is_auto_approved_by_votes,
            criteria_min_votes_required=event_with_all.criteria_min_votes_required,
            conclusion_approval_threshold_percent=event_with_all.conclusion_approval_threshold_percent,
            membership_is_auto_approved=event_with_all.membership_is_auto_approved,
            entrance_code=event_with_all.entrance_code,
        )

    def update_event(
        self,
        event_id: UUID,
        request: EventUpdateRequest,
        user_id: UUID
    ) -> Event:
        """이벤트 정보 수정"""
        # 관리자 권한 확인 및 이벤트 조회 - base 메서드 사용
        event = self.verify_admin(event_id, user_id)
        
        # 기본 정보 수정 (NOT_STARTED일 때만)
        if request.decision_subject is not None:
            self._validate_event_not_started(event, "modify decision subject")
            event.decision_subject = request.decision_subject
        
        # 선택지 업데이트 (NOT_STARTED일 때만)
        if request.options is not None:
            self._validate_event_not_started(event, "modify options")
            self._update_options(event_id, request.options, user_id)
        
        # 전제 업데이트 (NOT_STARTED일 때만)
        if request.assumptions is not None:
            self._validate_event_not_started(event, "modify assumptions")
            self._update_assumptions(event_id, request.assumptions, user_id)
        
        # 기준 업데이트 (NOT_STARTED일 때만)
        if request.criteria is not None:
            self._validate_event_not_started(event, "modify criteria")
            self._update_criteria(event_id, request.criteria, user_id)
        
        # 최대 인원 수정 (FINISHED가 아닐 때)
        if request.max_membership is not None:
            self._validate_event_not_finished(event, "modify max membership")
            # 현재 ACCEPTED 멤버 수 확인 - base 메서드 사용
            current_count = self.count_accepted_members(event_id)
            if request.max_membership < current_count:
                raise ValidationError(
                    message="Invalid max membership",
                    detail=f"Max membership ({request.max_membership}) cannot be less than current participant count ({current_count})"
                )
            event.max_membership = request.max_membership
        
        # 투표 허용 정책 수정 (FINISHED가 아닐 때)
        if request.assumption_is_auto_approved_by_votes is not None:
            self._validate_event_not_finished(event, "modify assumption auto approval policy")
            event.assumption_is_auto_approved_by_votes = request.assumption_is_auto_approved_by_votes
        
        if request.assumption_min_votes_required is not None:
            self._validate_event_not_finished(event, "modify assumption min votes required")
            event.assumption_min_votes_required = request.assumption_min_votes_required
        
        if request.criteria_is_auto_approved_by_votes is not None:
            self._validate_event_not_finished(event, "modify criteria auto approval policy")
            event.criteria_is_auto_approved_by_votes = request.criteria_is_auto_approved_by_votes
        
        if request.criteria_min_votes_required is not None:
            self._validate_event_not_finished(event, "modify criteria min votes required")
            event.criteria_min_votes_required = request.criteria_min_votes_required
        
        if request.conclusion_approval_threshold_percent is not None:
            self._validate_event_not_finished(event, "modify conclusion approval threshold")
            event.conclusion_approval_threshold_percent = request.conclusion_approval_threshold_percent
        
        # 입장 정책 수정 (FINISHED가 아닐 때)
        if request.membership_is_auto_approved is not None:
            self._validate_event_not_finished(event, "modify membership auto approval policy")
            event.membership_is_auto_approved = request.membership_is_auto_approved
        
        # 이벤트 업데이트
        with transaction(self.db):
            result = self.repos.event.update_event(event)
        return result

    def _update_options(
        self,
        event_id: UUID,
        option_items: List["OptionUpdateItem"],
        user_id: UUID
    ) -> None:
        """선택지 업데이트 처리"""
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
                option = self._validate_option_exists(item.id, event_id)
                self.repos.option.delete_option(option)
            else:
                # 수정
                option = self._validate_option_exists(item.id, event_id)
                option.content = item.content
                self.repos.option.update_option(option)

    def _update_assumptions(
        self,
        event_id: UUID,
        assumption_items: List["AssumptionUpdateItem"],
        user_id: UUID
    ) -> None:
        """전제 업데이트 처리"""
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
                assumption = self._validate_assumption_exists(item.id, event_id)
                self.repos.assumption.delete_assumption(assumption)
            else:
                # 수정
                assumption = self._validate_assumption_exists(item.id, event_id)
                assumption.content = item.content
                self.repos.assumption.update_assumption(assumption, user_id)

    def _update_criteria(
        self,
        event_id: UUID,
        criterion_items: List["CriterionUpdateItem"],
        user_id: UUID
    ) -> None:
        """기준 업데이트 처리"""
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
                criterion = self._validate_criterion_exists(item.id, event_id)
                self.repos.criterion.delete_criterion(criterion)
            else:
                # 수정
                criterion = self._validate_criterion_exists(item.id, event_id)
                criterion.content = item.content
                self.repos.criterion.update_criterion(criterion, user_id)

    def _validate_option_exists(self, option_id: UUID, event_id: UUID):
        """Option 존재 및 event_id 검증"""
        option = self.repos.option.get_by_id(option_id)
        if not option or option.event_id != event_id:
            raise NotFoundError(
                message="Option not found",
                detail=f"Option with id {option_id} not found for this event"
            )
        return option

    def _validate_assumption_exists(self, assumption_id: UUID, event_id: UUID):
        """Assumption 존재 및 event_id 검증"""
        assumption = self.repos.assumption.get_by_id(assumption_id)
        if not assumption or assumption.event_id != event_id:
            raise NotFoundError(
                message="Assumption not found",
                detail=f"Assumption with id {assumption_id} not found for this event"
            )
        return assumption

    def _validate_criterion_exists(self, criterion_id: UUID, event_id: UUID):
        """Criterion 존재 및 event_id 검증"""
        criterion = self.repos.criterion.get_by_id(criterion_id)
        if not criterion or criterion.event_id != event_id:
            raise NotFoundError(
                message="Criterion not found",
                detail=f"Criterion with id {criterion_id} not found for this event"
            )
        return criterion

    def update_event_status(
        self,
        event_id: UUID,
        new_status: EventStatusType,
        user_id: UUID
    ) -> EventStatusUpdateResponse:
        """
        이벤트 상태 변경 (관리자용)
        - 관리자 권한 확인
        - 상태 전이 규칙 검증:
          - NOT_STARTED → IN_PROGRESS (시작)
          - IN_PROGRESS → PAUSED (일시정지)
          - PAUSED → IN_PROGRESS (재개)
          - IN_PROGRESS → FINISHED (종료)
          - PAUSED → FINISHED (종료)
        """
        # 1. 관리자 권한 확인 및 이벤트 조회
        event = self.verify_admin(event_id, user_id)

        # 2. 현재 상태 확인
        current_status = event.event_status

        # 3. 상태 전이 규칙 검증
        valid_transitions = {
            EventStatusType.NOT_STARTED: [EventStatusType.IN_PROGRESS],
            EventStatusType.IN_PROGRESS: [EventStatusType.PAUSED, EventStatusType.FINISHED],
            EventStatusType.PAUSED: [EventStatusType.IN_PROGRESS, EventStatusType.FINISHED],
            EventStatusType.FINISHED: [],  # FINISHED는 종료 상태이므로 변경 불가
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                message="Invalid status transition",
                detail=f"Cannot change status from {current_status.value} to {new_status.value}"
            )

        # 4. 상태 변경
        with transaction(self.db):
            event.event_status = new_status
            event.updated_at = datetime.now(timezone.utc)
            result = self.repos.event.update_event(event)

        return EventStatusUpdateResponse(
            id=result.id,
            status=result.event_status,
            updated_at=result.updated_at
        )
