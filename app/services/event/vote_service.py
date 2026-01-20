from typing import List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.vote import OptionVote, CriterionPriority
from app.models.event import EventStatusType
from app.repositories.vote_repository import VoteRepository
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.services.event.base import EventBaseService
from app.schemas.event.vote import (
    VoteResponse,
    VoteViewResponse,
    VoteResultResponse,
    OptionVoteCount,
    CriterionRankInfo,
)
from app.schemas.event.common import OptionInfo
from app.schemas.event.setting import CriterionInfo
from app.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.utils.transaction import transaction


class VoteService(EventBaseService):
    """투표 관련 서비스"""
    
    def __init__(
        self,
        db: Session,
        repos: EventAggregateRepositories,
        vote_repo: VoteRepository
    ):
        super().__init__(db, repos)
        self.vote_repo = vote_repo
    
    def get_user_vote(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> VoteViewResponse:
        """사용자의 투표 내역 조회"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "view vote")
        
        # 이벤트 조회 (관계 포함)
        event = self.get_event_with_all_relations(event_id)

        # UI 표시용 정보 준비
        options = [
            OptionInfo(id=opt.id, content=opt.content)
            for opt in event.options
        ]
        
        criteria = [
            CriterionInfo(id=cr.id, content=cr.content)
            for cr in event.criteria
            if not cr.is_deleted  # 삭제되지 않은 기준만
        ]
        
        # 사용자의 선택지 투표 조회
        option_vote = self.vote_repo.get_user_option_vote(event_id, user_id)
        
        # 사용자의 기준 우선순위 조회 (priority_rank 오름차순)
        criterion_priorities = self.vote_repo.get_user_criterion_priorities(event_id, user_id)
        
        # 투표가 없는 경우
        if option_vote is None:
            # raise NotFoundError(
            #     message="Vote not found",
            #     detail="User has not voted yet"
            # )
            return VoteViewResponse(
                option_id=None,
                criterion_order=[],
                created_at=None,
                updated_at=None,
                decision_subject=event.decision_subject,
                options=options,
                criteria=criteria
            )
        else:
            # 기준 ID 리스트 생성 (priority_rank 순서대로)
            criterion_order = [cp.criterion_id for cp in criterion_priorities]
            
            # updated_at: CriterionPriority의 최신 updated_at 사용 (있으면)
            # 없으면 option_vote의 created_at 사용
            # (upsert 패턴으로 재투표 시 OptionVote는 새로 생성되므로 created_at이 최신 시간임)
            updated_at = None
            if criterion_priorities:
                # CriterionPriority의 updated_at 중 최신 값 사용
                updated_ats = [cp.updated_at for cp in criterion_priorities if cp.updated_at is not None]
                if updated_ats:
                    updated_at = max(updated_ats)
            
            # updated_at이 없으면 (초기 투표인 경우) option_vote의 created_at 사용
            if updated_at is None:
                updated_at = option_vote.created_at
            
            return VoteViewResponse(
                option_id=option_vote.option_id,
                criterion_order=criterion_order,
                created_at=option_vote.created_at,
                updated_at=updated_at,
                decision_subject=event.decision_subject,
                options=options,
                criteria=criteria
            )
    
    def create_or_update_vote(
        self,
        event_id: UUID,
        user_id: UUID,
        option_id: UUID,
        criterion_ids: List[UUID]
    ) -> VoteResponse:
        """투표 생성 또는 업데이트 (upsert 패턴)"""
        # 이벤트 조회 및 ACCEPTED 멤버십 확인
        event = self.get_event_with_all_relations(event_id)
        self._validate_membership_accepted(user_id, event_id, "vote")
        
        # IN_PROGRESS 상태에서만 투표 가능
        if event.event_status != EventStatusType.IN_PROGRESS:
            raise ValidationError(
                message="Event not in progress",
                detail="Voting is only allowed when event status is IN_PROGRESS"
            )
        
        # option이 해당 event에 속하는지 확인
        option = self.repos.option.get_by_id(option_id)
        if not option:
            raise NotFoundError(
                message="Option not found",
                detail=f"Option with id {option_id} not found"
            )
        if option.event_id != event_id:
            raise ValidationError(
                message="Invalid option",
                detail=f"Option {option_id} does not belong to event {event_id}"
            )
        
        # criterion_ids의 모든 criterion이 해당 event에 속하는지 확인
        if not criterion_ids:
            raise ValidationError(
                message="Invalid criterion_ids",
                detail="criterion_ids cannot be empty"
            )
        
        # 중복 확인
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValidationError(
                message="Invalid criterion_ids",
                detail="criterion_ids contains duplicates"
            )
        
        # 모든 활성화된 criterion 목록 (삭제되지 않은 것만)
        active_criteria = [cr for cr in event.criteria if not cr.is_deleted]
        active_criterion_ids = {cr.id for cr in active_criteria}
        
        # 재투표 시 모든 활성화된 criterion이 포함되어야 함
        provided_criterion_ids = set(criterion_ids)
        if provided_criterion_ids != active_criterion_ids:
            missing_criteria = active_criterion_ids - provided_criterion_ids
            extra_criteria = provided_criterion_ids - active_criterion_ids
            error_details = []
            if missing_criteria:
                error_details.append(f"Missing criteria: {list(missing_criteria)}")
            if extra_criteria:
                error_details.append(f"Invalid or deleted criteria: {list(extra_criteria)}")
            raise ValidationError(
                message="Invalid criterion_ids",
                detail=f"All active criteria must be included. {'; '.join(error_details)}"
            )
        
        # 모든 criterion 존재 및 이벤트 소속 확인 (이미 active_criteria에서 확인했지만 추가 검증)
        for criterion_id in criterion_ids:
            criterion = self.repos.criterion.get_by_id(criterion_id)
            if not criterion:
                raise NotFoundError(
                    message="Criterion not found",
                    detail=f"Criterion with id {criterion_id} not found"
                )
            if criterion.event_id != event_id:
                raise ValidationError(
                    message="Invalid criterion",
                    detail=f"Criterion {criterion_id} does not belong to event {event_id}"
                )
        
        # 기존 투표 삭제 및 새 투표 생성
        existing_option_vote = self.vote_repo.get_user_option_vote(event_id, user_id)
        existing_criterion_priorities = self.vote_repo.get_user_criterion_priorities(event_id, user_id)
        
        now = datetime.now(timezone.utc)
        
        with transaction(self.db):
            # 기존 OptionVote 삭제 (있는 경우)
            if existing_option_vote:
                self.vote_repo.delete_option_vote(existing_option_vote)
            
            # 기존 CriterionPriority 삭제 (있는 경우)
            if existing_criterion_priorities:
                self.vote_repo.delete_criterion_priorities(existing_criterion_priorities)
            
            # 새로운 OptionVote 생성
            new_option_vote = OptionVote(
                option_id=option_id,
                created_by=user_id
            )
            self.vote_repo.create_option_vote(new_option_vote)
            
            # 새로운 CriterionPriority 목록 생성 (순서대로 priority_rank 부여: 인덱스 + 1)
            new_criterion_priorities = []
            for index, criterion_id in enumerate(criterion_ids, start=1):
                priority = CriterionPriority(
                    criterion_id=criterion_id,
                    created_by=user_id,
                    priority_rank=index,
                    updated_at=now  # 업데이트 시간 기록
                )
                new_criterion_priorities.append(priority)
            
            self.vote_repo.create_criterion_priorities(new_criterion_priorities)
        
        # 응답 반환 (기본 투표 정보만)
        return VoteResponse(
            option_id=new_option_vote.option_id,
            criterion_order=criterion_ids,
            created_at=new_option_vote.created_at,
            updated_at=now
        )
    
    def get_vote_result(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> VoteResultResponse:
        """
        투표 결과 조회
        - FINISHED 상태에서만 가능
        - ACCEPTED 멤버십 필요
        """
        # 이벤트 조회 및 ACCEPTED 멤버십 확인
        event = self.get_event_with_all_relations(event_id)
        self._validate_membership_accepted(user_id, event_id, "view vote results")
        
        # FINISHED 상태에서만 조회 가능
        if event.event_status != EventStatusType.FINISHED:
            raise ValidationError(
                message="Event not finished",
                detail="Vote results can only be viewed when event status is FINISHED"
            )
        
        # 전체 참가 인원 수 (ACCEPTED 멤버십)
        total_participants_count = self.count_accepted_members(event_id)
        
        # 투표 참여 인원 수
        voted_participants_count = self.vote_repo.count_voted_users(event_id)
        
        # 옵션별 투표 수
        option_vote_counts_raw = self.vote_repo.get_option_vote_counts(event_id)
        option_vote_counts = [
            OptionVoteCount(
                option_id=option_id,
                option_content=content,
                vote_count=count
            )
            for option_id, content, count in option_vote_counts_raw
        ]
        
        # 1순위로 가장 많이 꼽힌 기준
        first_priority_raw = self.vote_repo.get_first_priority_criteria_counts(event_id)
        first_priority_criteria = [
            CriterionRankInfo(
                criterion_id=criterion_id,
                criterion_content=content,
                count=count
            )
            for criterion_id, content, count in first_priority_raw
        ]
        
        # 우선순위별 가중치 부여한 기준
        weighted_raw = self.vote_repo.get_weighted_criteria_scores(event_id)
        weighted_criteria = [
            CriterionRankInfo(
                criterion_id=criterion_id,
                criterion_content=content,
                count=score  # 가중치 점수
            )
            for criterion_id, content, score in weighted_raw
        ]
        
        return VoteResultResponse(
            total_participants_count=total_participants_count,
            voted_participants_count=voted_participants_count,
            option_vote_counts=option_vote_counts,
            first_priority_criteria=first_priority_criteria,
            weighted_criteria=weighted_criteria,
        )