from typing import List
from sqlalchemy.orm import Session

from app.models.content import Criterion
from uuid import UUID

class CriterionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_criteria(self, criteria: List[Criterion]) -> List[Criterion]:
        """기준들을 생성"""
        self.db.add_all(criteria)
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
        for criterion in criteria:
            self.db.refresh(criterion)
        return criteria

    def get_by_id(self, criterion_id: UUID) -> Criterion | None:
        """기준 ID로 조회"""
        from sqlalchemy import select
        from uuid import UUID
        stmt = select(Criterion).where(Criterion.id == criterion_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_criterion(self, criterion: Criterion, updated_by: UUID) -> Criterion:
        """기준 업데이트"""
        from datetime import datetime, timezone
        criterion.updated_at = datetime.now(timezone.utc)
        criterion.updated_by = updated_by
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(criterion)
        return criterion

    def delete_criterion(self, criterion: Criterion) -> None:
        """기준 삭제"""
        self.db.delete(criterion)
        # commit은 Service에서 수행
