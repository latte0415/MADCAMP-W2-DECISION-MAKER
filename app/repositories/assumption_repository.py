from typing import List
from sqlalchemy.orm import Session

from uuid import UUID
from app.models.content import Assumption


class AssumptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_assumptions(self, assumptions: List[Assumption]) -> List[Assumption]:
        """전제들을 생성"""
        self.db.add_all(assumptions)
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
        for assumption in assumptions:
            self.db.refresh(assumption)
        return assumptions

    def get_by_id(self, assumption_id: UUID) -> Assumption | None:
        """전제 ID로 조회"""
        from sqlalchemy import select
        stmt = select(Assumption).where(Assumption.id == assumption_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_assumption(self, assumption: Assumption, updated_by: UUID) -> Assumption:
        """전제 업데이트"""
        from datetime import datetime, timezone
        assumption.updated_at = datetime.now(timezone.utc)
        assumption.updated_by = updated_by
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(assumption)
        return assumption

    def delete_assumption(self, assumption: Assumption) -> None:
        """전제 삭제"""
        self.db.delete(assumption)
        # commit은 Service에서 수행
