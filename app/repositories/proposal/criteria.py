from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, func as sql_func
from sqlalchemy.orm import Session, joinedload

from app.models.proposal import CriteriaProposal, ProposalStatusType
from app.models.vote import CriterionProposalVote
from app.repositories.proposal.generic import ProposalRepositoryGeneric


class CriteriaProposalRepository(ProposalRepositoryGeneric):
    """CriteriaProposal 전용 리포지토리"""

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

    def create_criteria_proposal(
        self, proposal: CriteriaProposal
    ) -> CriteriaProposal:
        """기준 제안 생성"""
        return self.create_proposal_generic(proposal)

    def get_criteria_proposal_by_id(
        self, proposal_id: UUID
    ) -> CriteriaProposal | None:
        """기준 제안 ID로 조회"""
        return self.get_proposal_by_id_generic(
            proposal_id,
            CriteriaProposal,
            relationships=['votes', 'creator', 'criterion']
        )

    def get_pending_criteria_proposal_by_user(
        self,
        event_id: UUID,
        criteria_id: UUID | None,
        user_id: UUID
    ) -> CriteriaProposal | None:
        """
        사용자의 PENDING 상태 기준 제안 조회 (중복 체크용)
        - criteria_id가 None이면 CREATION 제안
        - criteria_id가 있으면 MODIFICATION/DELETION 제안
        """
        stmt = (
            select(CriteriaProposal)
            .where(
                CriteriaProposal.event_id == event_id,
                CriteriaProposal.criteria_id == criteria_id,
                CriteriaProposal.created_by == user_id,
                CriteriaProposal.proposal_status == ProposalStatusType.PENDING
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_criteria_proposal(
        self, proposal: CriteriaProposal
    ) -> CriteriaProposal:
        """기준 제안 업데이트"""
        return self.update_proposal_generic(proposal)

    def approve_criteria_proposal_if_pending(
        self, proposal_id: UUID, accepted_at: datetime
    ) -> CriteriaProposal | None:
        """PENDING 상태인 기준 제안을 조건부로 승인"""
        return self.approve_proposal_if_pending_generic(
            proposal_id, accepted_at, CriteriaProposal
        )

    def reject_criteria_proposal_if_pending(
        self, proposal_id: UUID
    ) -> CriteriaProposal | None:
        """PENDING 상태인 기준 제안을 조건부로 거절"""
        return self.reject_proposal_if_pending_generic(
            proposal_id, CriteriaProposal
        )

    def get_user_vote_on_criteria_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> CriterionProposalVote | None:
        """사용자가 특정 기준 제안에 투표했는지 확인"""
        stmt = select(CriterionProposalVote).where(
            CriterionProposalVote.criterion_proposal_id == proposal_id,
            CriterionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_votes_on_criteria_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: UUID
    ) -> dict[UUID, CriterionProposalVote]:
        """여러 기준 제안에 대한 사용자 투표를 한 번에 조회"""
        if not proposal_ids:
            return {}
        stmt = select(CriterionProposalVote).where(
            CriterionProposalVote.criterion_proposal_id.in_(proposal_ids),
            CriterionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        votes = result.scalars().all()
        return {vote.criterion_proposal_id: vote for vote in votes}

    def create_criteria_proposal_vote(
        self, vote: CriterionProposalVote
    ) -> CriterionProposalVote:
        """기준 제안 투표 생성"""
        self.db.add(vote)
        self.db.flush()
        return vote

    def delete_criteria_proposal_vote(
        self, vote: CriterionProposalVote
    ) -> None:
        """기준 제안 투표 삭제"""
        self.db.delete(vote)
        self.db.flush()

    def count_criteria_proposal_votes(
        self, proposal_id: UUID
    ) -> int:
        """기준 제안 투표 수 조회"""
        stmt = (
            select(sql_func.count(CriterionProposalVote.id))
            .where(CriterionProposalVote.criterion_proposal_id == proposal_id)
        )
        result = self.db.execute(stmt)
        return result.scalar() or 0
