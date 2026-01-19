from uuid import UUID
from typing import List, TYPE_CHECKING
from typing import List

from app.models.event import Event, EventStatusType
from app.models.content import Assumption, Criterion
from app.services.event.base import EventBaseService
from app.schemas.event import (
    EventSettingResponse,
    EventUpdateRequest,
    EventResponse,
    OptionInfo,
    AssumptionInfo,
    CriterionInfo,
)
from app.exceptions import NotFoundError, ValidationError

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
        from app.models.event import Option
        
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
