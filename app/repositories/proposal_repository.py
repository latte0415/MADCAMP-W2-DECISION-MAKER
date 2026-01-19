from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

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
            AssumptionProposalVote.assumption_proposal_id == proposal_id,
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
            CriterionProposalVote.criterion_proposal_id == proposal_id,
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

    def get_user_votes_on_conclusion_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: UUID
    ) -> dict[UUID, ConclusionProposalVote]:
        """여러 결론 제안에 대한 사용자 투표를 한 번에 조회"""
        if not proposal_ids:
            return {}
        stmt = select(ConclusionProposalVote).where(
            ConclusionProposalVote.proposal_id.in_(proposal_ids),
            ConclusionProposalVote.created_by == user_id
        )
        result = self.db.execute(stmt)
        votes = result.scalars().all()
        return {vote.proposal_id: vote for vote in votes}

    # ============================================================================
    # Assumption Proposal CRUD
    # ============================================================================

    def create_assumption_proposal(
        self, proposal: AssumptionProposal
    ) -> AssumptionProposal:
        """전제 제안 생성"""
        self.db.add(proposal)
        self.db.flush()
        return proposal

    def get_assumption_proposal_by_id(
        self, proposal_id: UUID
    ) -> AssumptionProposal | None:
        """전제 제안 ID로 조회"""
        stmt = (
            select(AssumptionProposal)
            .where(AssumptionProposal.id == proposal_id)
            .options(
                joinedload(AssumptionProposal.votes),
                joinedload(AssumptionProposal.creator),
                joinedload(AssumptionProposal.assumption)
            )
        )
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

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
        self.db.flush()
        return proposal

    def approve_assumption_proposal_if_pending(
        self, proposal_id: UUID, accepted_at: datetime
    ) -> AssumptionProposal | None:
        """
        PENDING 상태인 전제 제안을 조건부로 승인
        - WHERE id = :id AND status = 'PENDING' 조건으로 업데이트
        - 이미 승인된 경우 None 반환 (중복 승인 방지)
        - 성공 시 업데이트된 proposal 반환
        """
        stmt = (
            update(AssumptionProposal)
            .where(
                AssumptionProposal.id == proposal_id,
                AssumptionProposal.proposal_status == ProposalStatusType.PENDING
            )
            .values(
                proposal_status=ProposalStatusType.ACCEPTED,
                accepted_at=accepted_at
            )
            .returning(AssumptionProposal)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()

    # ============================================================================
    # Assumption Proposal Vote CRUD
    # ============================================================================

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
        from sqlalchemy import func as sql_func
        stmt = (
            select(sql_func.count(AssumptionProposalVote.id))
            .where(AssumptionProposalVote.assumption_proposal_id == proposal_id)
        )
        result = self.db.execute(stmt)
        return result.scalar() or 0

    # ============================================================================
    # Criteria Proposal CRUD
    # ============================================================================

    def create_criteria_proposal(
        self, proposal: CriteriaProposal
    ) -> CriteriaProposal:
        """기준 제안 생성"""
        self.db.add(proposal)
        self.db.flush()
        return proposal

    def get_criteria_proposal_by_id(
        self, proposal_id: UUID
    ) -> CriteriaProposal | None:
        """기준 제안 ID로 조회"""
        stmt = (
            select(CriteriaProposal)
            .where(CriteriaProposal.id == proposal_id)
            .options(
                joinedload(CriteriaProposal.votes),
                joinedload(CriteriaProposal.creator),
                joinedload(CriteriaProposal.criterion)
            )
        )
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

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
        self.db.flush()
        return proposal

    def approve_criteria_proposal_if_pending(
        self, proposal_id: UUID, accepted_at: datetime
    ) -> CriteriaProposal | None:
        """
        PENDING 상태인 기준 제안을 조건부로 승인
        - WHERE id = :id AND status = 'PENDING' 조건으로 업데이트
        - 이미 승인된 경우 None 반환 (중복 승인 방지)
        - 성공 시 업데이트된 proposal 반환
        """
        stmt = (
            update(CriteriaProposal)
            .where(
                CriteriaProposal.id == proposal_id,
                CriteriaProposal.proposal_status == ProposalStatusType.PENDING
            )
            .values(
                proposal_status=ProposalStatusType.ACCEPTED,
                accepted_at=accepted_at
            )
            .returning(CriteriaProposal)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()

    # ============================================================================
    # Criteria Proposal Vote CRUD
    # ============================================================================

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
        from sqlalchemy import func as sql_func
        stmt = (
            select(sql_func.count(CriterionProposalVote.id))
            .where(CriterionProposalVote.criterion_proposal_id == proposal_id)
        )
        result = self.db.execute(stmt)
        return result.scalar() or 0
