from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, func as sql_func
from sqlalchemy.orm import Session, joinedload

from app.models.proposal import AssumptionProposal, ProposalStatusType
from app.models.vote import AssumptionProposalVote
from app.repositories.proposal.generic import ProposalRepositoryGeneric


class AssumptionProposalRepository(ProposalRepositoryGeneric):
    """AssumptionProposal 전용 리포지토리"""

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

    def create_assumption_proposal(
        self, proposal: AssumptionProposal
    ) -> AssumptionProposal:
        """전제 제안 생성"""
        return self.create_proposal_generic(proposal)

    def get_assumption_proposal_by_id(
        self, proposal_id: UUID
    ) -> AssumptionProposal | None:
        """전제 제안 ID로 조회"""
        return self.get_proposal_by_id_generic(
            proposal_id,
            AssumptionProposal,
            relationships=['votes', 'creator', 'assumption']
        )

    def get_pending_assumption_proposal_by_user(
        self,
        event_id: UUID,
        assumption_id: UUID | None,
        user_id: UUID
    ) -> AssumptionProposal | None:
        """
        사용자의 PENDING 상태 전제 제안 조회 (중복 체크용)
        - assumption_id가 None이면 CREATION 제안
        - assumption_id가 있으면 MODIFICATION/DELETION 제안
        """
        stmt = (
            select(AssumptionProposal)
            .where(
                AssumptionProposal.event_id == event_id,
                AssumptionProposal.assumption_id == assumption_id,
                AssumptionProposal.created_by == user_id,
                AssumptionProposal.proposal_status == ProposalStatusType.PENDING
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_assumption_proposal(
        self, proposal: AssumptionProposal
    ) -> AssumptionProposal:
        """전제 제안 업데이트"""
        return self.update_proposal_generic(proposal)

    def approve_assumption_proposal_if_pending(
        self, proposal_id: UUID, accepted_at: datetime
    ) -> AssumptionProposal | None:
        """PENDING 상태인 전제 제안을 조건부로 승인"""
        return self.approve_proposal_if_pending_generic(
            proposal_id, accepted_at, AssumptionProposal
        )

    def get_user_vote_on_assumption_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> AssumptionProposalVote | None:
        """사용자가 특정 전제 제안에 투표했는지 확인"""
        stmt = select(AssumptionProposalVote).where(
            AssumptionProposalVote.assumption_proposal_id == proposal_id,
            AssumptionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_votes_on_assumption_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: UUID
    ) -> dict[UUID, AssumptionProposalVote]:
        """여러 전제 제안에 대한 사용자 투표를 한 번에 조회"""
        if not proposal_ids:
            return {}
        stmt = select(AssumptionProposalVote).where(
            AssumptionProposalVote.assumption_proposal_id.in_(proposal_ids),
            AssumptionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        votes = result.scalars().all()
        return {vote.assumption_proposal_id: vote for vote in votes}

    def create_assumption_proposal_vote(
        self, vote: AssumptionProposalVote
    ) -> AssumptionProposalVote:
        """전제 제안 투표 생성"""
        self.db.add(vote)
        self.db.flush()
        return vote

    def delete_assumption_proposal_vote(
        self, vote: AssumptionProposalVote
    ) -> None:
        """전제 제안 투표 삭제"""
        self.db.delete(vote)
        self.db.flush()

    def count_assumption_proposal_votes(
        self, proposal_id: UUID
    ) -> int:
        """전제 제안 투표 수 조회"""
        stmt = (
            select(sql_func.count(AssumptionProposalVote.id))
            .where(AssumptionProposalVote.assumption_proposal_id == proposal_id)
        )
        result = self.db.execute(stmt)
        return result.scalar() or 0
