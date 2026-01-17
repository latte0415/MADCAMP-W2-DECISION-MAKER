from typing import List
from sqlalchemy.orm import Session

from app.models.content import Assumption


class AssumptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_assumptions(self, assumptions: List[Assumption]) -> List[Assumption]:
        """전제들을 생성"""
        self.db.add_all(assumptions)
        self.db.commit()
        for assumption in assumptions:
            self.db.refresh(assumption)
        return assumptions
