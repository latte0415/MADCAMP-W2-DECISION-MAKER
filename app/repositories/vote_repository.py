from typing import List, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, distinct, case

from app.models.vote import OptionVote, CriterionPriority
from app.models.event import Option
from app.models.content import Criterion


class VoteRepository:
    """최종 투표 관련 리포지토리 (OptionVote, CriterionPriority)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_option_vote(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> OptionVote | None:
        """사용자의 특정 이벤트에 대한 선택지 투표 조회"""
        stmt = (
            select(OptionVote)
            .join(Option, OptionVote.option_id == Option.id)
            .where(
                and_(
                    Option.event_id == event_id,
                    OptionVote.created_by == user_id
                )
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_user_criterion_priorities(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> List[CriterionPriority]:
        """사용자의 특정 이벤트에 대한 기준 우선순위 목록 조회 (priority_rank 오름차순)"""
        stmt = (
            select(CriterionPriority)
            .join(Criterion, CriterionPriority.criterion_id == Criterion.id)
            .where(
                and_(
                    Criterion.event_id == event_id,
                    CriterionPriority.created_by == user_id
                )
            )
            .order_by(CriterionPriority.priority_rank.asc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def create_option_vote(
        self,
        vote: OptionVote
    ) -> OptionVote:
        """선택지 투표 생성"""
        self.db.add(vote)
        self.db.flush()
        self.db.refresh(vote)
        return vote
    
    def delete_option_vote(
        self,
        vote: OptionVote
    ) -> None:
        """선택지 투표 삭제"""
        self.db.delete(vote)
        self.db.flush()
    
    def create_criterion_priorities(
        self,
        priorities: List[CriterionPriority]
    ) -> List[CriterionPriority]:
        """기준 우선순위 목록 생성"""
        self.db.add_all(priorities)
        self.db.flush()
        for priority in priorities:
            self.db.refresh(priority)
        return priorities
    
    def delete_criterion_priorities(
        self,
        priorities: List[CriterionPriority]
    ) -> None:
        """기준 우선순위 목록 삭제"""
        for priority in priorities:
            self.db.delete(priority)
        self.db.flush()
    
    def count_voted_users(self, event_id: UUID) -> int:
        """이벤트의 최종 투표를 완료한 사용자 수 카운트 (중복 제거)"""
        stmt = (
            select(func.count(distinct(OptionVote.created_by)))
            .join(Option, OptionVote.option_id == Option.id)
            .where(Option.event_id == event_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one() or 0
    
    def get_option_vote_counts(self, event_id: UUID) -> List[Tuple[UUID, str, int]]:
        """옵션별 투표 수 조회 (option_id, option_content, vote_count)"""
        stmt = (
            select(
                Option.id,
                Option.content,
                func.count(OptionVote.id).label('vote_count')
            )
            .outerjoin(OptionVote, Option.id == OptionVote.option_id)
            .where(Option.event_id == event_id)
            .group_by(Option.id, Option.content)
            .order_by(Option.id)
        )
        result = self.db.execute(stmt)
        return [(row.id, row.content, row.vote_count or 0) for row in result.all()]
    
    def get_first_priority_criteria_counts(self, event_id: UUID) -> List[Tuple[UUID, str, int]]:
        """1순위로 가장 많이 꼽힌 기준 조회 (criterion_id, criterion_content, count)"""
        stmt = (
            select(
                Criterion.id,
                Criterion.content,
                func.count(CriterionPriority.id).label('count')
            )
            .join(CriterionPriority, Criterion.id == CriterionPriority.criterion_id)
            .where(
                and_(
                    Criterion.event_id == event_id,
                    CriterionPriority.priority_rank == 1  # 1순위만
                )
            )
            .group_by(Criterion.id, Criterion.content)
            .order_by(func.count(CriterionPriority.id).desc())
        )
        result = self.db.execute(stmt)
        return [(row.id, row.content, row.count) for row in result.all()]
    
    def get_weighted_criteria_scores(self, event_id: UUID) -> List[Tuple[UUID, str, int]]:
        """우선순위별 가중치 부여한 기준 점수 조회 (criterion_id, criterion_content, weighted_score)"""
        # 가중치: 1위=3점, 2위=2점, 3위=1점, 4위 이상=0점
        weighted_score_expr = func.sum(
            case(
                (CriterionPriority.priority_rank == 1, 3),
                (CriterionPriority.priority_rank == 2, 2),
                (CriterionPriority.priority_rank == 3, 1),
                else_=0
            )
        )
        stmt = (
            select(
                Criterion.id,
                Criterion.content,
                weighted_score_expr.label('weighted_score')
            )
            .join(CriterionPriority, Criterion.id == CriterionPriority.criterion_id)
            .where(Criterion.event_id == event_id)
            .group_by(Criterion.id, Criterion.content)
            .order_by(weighted_score_expr.desc())
        )
        result = self.db.execute(stmt)
        return [(row.id, row.content, row.weighted_score or 0) for row in result.all()]