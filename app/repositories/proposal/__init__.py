"""
Proposal 리포지토리 모듈
- 제너릭 메서드와 각 타입별 리포지토리를 통합하여 export
"""
from sqlalchemy.orm import Session

from app.repositories.proposal.assumption import AssumptionProposalRepository
from app.repositories.proposal.criteria import CriteriaProposalRepository
from app.repositories.proposal.conclusion import ConclusionProposalRepository
from app.repositories.proposal.generic import (
    ProposalRepositoryGeneric,
    ProposalType,
)

# 통합 리포지토리
class ProposalRepository(
    AssumptionProposalRepository,
    CriteriaProposalRepository,
    ConclusionProposalRepository
):
    """
    통합 Proposal 리포지토리
    - 각 타입별 리포지토리를 상속받아 모든 메서드를 제공
    - 제너릭 메서드는 각 리포지토리에서 ProposalRepositoryGeneric을 통해 제공됨
    """

    def __init__(self, db: Session):
        # 모든 부모 클래스의 __init__ 호출
        AssumptionProposalRepository.__init__(self, db)
        CriteriaProposalRepository.__init__(self, db)
        ConclusionProposalRepository.__init__(self, db)


# Export
__all__ = [
    "ProposalRepository",
    "ProposalRepositoryGeneric",
    "ProposalType",
    "AssumptionProposalRepository",
    "CriteriaProposalRepository",
    "ConclusionProposalRepository",
]
