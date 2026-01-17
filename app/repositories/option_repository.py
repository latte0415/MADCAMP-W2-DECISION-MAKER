from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Option


class OptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_options(self, options: List[Option]) -> List[Option]:
        """선택지들을 생성"""
        self.db.add_all(options)
        self.db.commit()
        for option in options:
            self.db.refresh(option)
        return options
