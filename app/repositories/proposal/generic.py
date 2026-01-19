from datetime import datetime
from typing import TypeVar, Type
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.proposal import ProposalBase, ProposalStatusType

# TypeVar 정의
ProposalType = TypeVar('ProposalType', bound=ProposalBase)


class ProposalRepositoryGeneric:
    """Proposal 리포지토리의 제너릭 메서드를 제공하는 Base 클래스"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_proposal_generic(
        self, proposal: ProposalType
    ) -> ProposalType:
        """제너릭 제안 생성"""
        self.db.add(proposal)
        self.db.flush()
        return proposal

    def get_proposal_by_id_generic(
        self,
        proposal_id: UUID,
        proposal_class: Type[ProposalType],
        relationships: list[str] | None = None
    ) -> ProposalType | None:
        """제너릭 제안 조회"""
        stmt = select(proposal_class).where(proposal_class.id == proposal_id)
        if relationships:
            for rel in relationships:
                stmt = stmt.options(joinedload(getattr(proposal_class, rel)))
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def update_proposal_generic(
        self, proposal: ProposalType
    ) -> ProposalType:
        """제너릭 제안 업데이트"""
        self.db.flush()
        return proposal

    def approve_proposal_if_pending_generic(
        self,
        proposal_id: UUID,
        accepted_at: datetime,
        proposal_class: Type[ProposalType]
    ) -> ProposalType | None:
        """
        제너릭 조건부 승인
        - WHERE id = :id AND status = 'PENDING' 조건으로 업데이트
        - 이미 승인된 경우 None 반환 (중복 승인 방지)
        - 성공 시 업데이트된 proposal 반환
        """
        stmt = (
            update(proposal_class)
            .where(
                proposal_class.id == proposal_id,
                proposal_class.proposal_status == ProposalStatusType.PENDING
            )
            .values(
                proposal_status=ProposalStatusType.ACCEPTED,
                accepted_at=accepted_at
            )
            .returning(proposal_class)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()
