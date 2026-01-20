from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, func as sql_func
from sqlalchemy.orm import Session, joinedload

from app.models.proposal import ConclusionProposal, ProposalStatusType
from app.models.vote import ConclusionProposalVote
from app.repositories.proposal.generic import ProposalRepositoryGeneric


class ConclusionProposalRepository(ProposalRepositoryGeneric):
    """ConclusionProposal 전용 리포지토리"""

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

    def create_conclusion_proposal(
        self, proposal: ConclusionProposal
    ) -> ConclusionProposal:
        """결론 제안 생성"""
        return self.create_proposal_generic(proposal)

    def get_conclusion_proposal_by_id(
        self, proposal_id: UUID
    ) -> ConclusionProposal | None:
        """결론 제안 ID로 조회"""
        return self.get_proposal_by_id_generic(
            proposal_id,
            ConclusionProposal,
            relationships=['votes', 'creator', 'criterion']
        )

    def get_pending_conclusion_proposal_by_user(
        self,
        criterion_id: UUID,
        user_id: UUID
    ) -> ConclusionProposal | None:
        """
        사용자의 PENDING 상태 결론 제안 조회 (중복 체크용)
        """
        stmt = (
            select(ConclusionProposal)
            .where(
                ConclusionProposal.criterion_id == criterion_id,
                ConclusionProposal.created_by == user_id,
                ConclusionProposal.proposal_status == ProposalStatusType.PENDING
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_conclusion_proposal(
        self, proposal: ConclusionProposal
    ) -> ConclusionProposal:
        """결론 제안 업데이트"""
        return self.update_proposal_generic(proposal)

    def approve_conclusion_proposal_if_pending(
        self, proposal_id: UUID, accepted_at: datetime
    ) -> ConclusionProposal | None:
        """PENDING 상태인 결론 제안을 조건부로 승인"""
        return self.approve_proposal_if_pending_generic(
            proposal_id, accepted_at, ConclusionProposal
        )

    def reject_conclusion_proposal_if_pending(
        self, proposal_id: UUID
    ) -> ConclusionProposal | None:
        """PENDING 상태인 결론 제안을 조건부로 거절"""
        return self.reject_proposal_if_pending_generic(
            proposal_id, ConclusionProposal
        )

    def get_user_vote_on_conclusion_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> ConclusionProposalVote | None:
        """사용자가 특정 결론 제안에 투표했는지 확인"""
        stmt = select(ConclusionProposalVote).where(
            ConclusionProposalVote.conclusion_proposal_id == proposal_id,
            ConclusionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_votes_on_conclusion_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: UUID
    ) -> dict[UUID, ConclusionProposalVote]:
        """여러 결론 제안에 대한 사용자 투표를 한 번에 조회"""
        if not proposal_ids:
            return {}
        stmt = select(ConclusionProposalVote).where(
            ConclusionProposalVote.conclusion_proposal_id.in_(proposal_ids),
            ConclusionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        votes = result.scalars().all()
        return {vote.conclusion_proposal_id: vote for vote in votes}

    def create_conclusion_proposal_vote(
        self, vote: ConclusionProposalVote
    ) -> ConclusionProposalVote:
        """결론 제안 투표 생성"""
        self.db.add(vote)
        self.db.flush()
        return vote

    def delete_conclusion_proposal_vote(
        self, vote: ConclusionProposalVote
    ) -> None:
        """결론 제안 투표 삭제"""
        self.db.delete(vote)
        self.db.flush()

    def count_conclusion_proposal_votes(
        self, proposal_id: UUID
    ) -> int:
        """결론 제안 투표 수 조회"""
        stmt = (
            select(sql_func.count(ConclusionProposalVote.id))
            .where(ConclusionProposalVote.conclusion_proposal_id == proposal_id)
        )
        result = self.db.execute(stmt)
        return result.scalar() or 0
