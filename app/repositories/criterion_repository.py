from typing import List
from sqlalchemy.orm import Session

from app.models.content import Criterion


class CriterionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_criteria(self, criteria: List[Criterion]) -> List[Criterion]:
        """기준들을 생성"""
        self.db.add_all(criteria)
        self.db.commit()
        for criterion in criteria:
            self.db.refresh(criterion)
        return criteria
