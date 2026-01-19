from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.proposal import (
    AssumptionProposal,
    CriteriaProposal,
    ConclusionProposal,
    ProposalStatusType,
)
from app.models.vote import (
    AssumptionProposalVote,
    CriterionProposalVote,
    ConclusionProposalVote,
)


class ProposalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_assumption_proposals_by_event_id(
        self,
        event_id: UUID,
        user_id: UUID | None = None
    ) -> List[AssumptionProposal]:
        """
        이벤트의 전제 제안 목록 조회
        - votes와 creator를 조인하여 가져옴
        - user_id가 제공되면 해당 사용자의 투표 여부도 포함
        """
        stmt = (
            select(AssumptionProposal)
            .where(AssumptionProposal.event_id == event_id)
            .options(
                joinedload(AssumptionProposal.votes),
                joinedload(AssumptionProposal.creator),
                joinedload(AssumptionProposal.assumption)
            )
            .order_by(AssumptionProposal.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.unique().scalars().all())

    def get_criteria_proposals_by_event_id(
        self,
        event_id: UUID,
        user_id: UUID | None = None
    ) -> List[CriteriaProposal]:
        """
        이벤트의 기준 제안 목록 조회
        - votes와 creator를 조인하여 가져옴
        - user_id가 제공되면 해당 사용자의 투표 여부도 포함
        """
        stmt = (
            select(CriteriaProposal)
            .where(CriteriaProposal.event_id == event_id)
            .options(
                joinedload(CriteriaProposal.votes),
                joinedload(CriteriaProposal.creator),
                joinedload(CriteriaProposal.criterion)
            )
            .order_by(CriteriaProposal.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.unique().scalars().all())

    def get_conclusion_proposals_by_criterion_id(
        self,
        criterion_id: UUID,
        user_id: UUID | None = None
    ) -> List[ConclusionProposal]:
        """
        특정 기준의 결론 제안 목록 조회
        - votes와 creator를 조인하여 가져옴
        """
        stmt = (
            select(ConclusionProposal)
            .where(ConclusionProposal.criterion_id == criterion_id)
            .options(
                joinedload(ConclusionProposal.votes),
                joinedload(ConclusionProposal.creator)
            )
            .order_by(ConclusionProposal.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.unique().scalars().all())

    def get_user_vote_on_assumption_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> AssumptionProposalVote | None:
        """사용자가 특정 전제 제안에 투표했는지 확인"""
        stmt = select(AssumptionProposalVote).where(
            AssumptionProposalVote.proposal_id == proposal_id,
            AssumptionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_vote_on_criteria_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> CriterionProposalVote | None:
        """사용자가 특정 기준 제안에 투표했는지 확인"""
        stmt = select(CriterionProposalVote).where(
            CriterionProposalVote.proposal_id == proposal_id,
            CriterionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_vote_on_conclusion_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> ConclusionProposalVote | None:
        """사용자가 특정 결론 제안에 투표했는지 확인"""
        stmt = select(ConclusionProposalVote).where(
            ConclusionProposalVote.proposal_id == proposal_id,
            ConclusionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
