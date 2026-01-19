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
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
        for option in options:
            self.db.refresh(option)
        return options

    def get_by_id(self, option_id: UUID) -> Option | None:
        """선택지 ID로 조회"""
        from sqlalchemy import select
        stmt = select(Option).where(Option.id == option_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_option(self, option: Option) -> Option:
        """선택지 업데이트"""
        from datetime import datetime, timezone
        option.updated_at = datetime.now(timezone.utc)
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(option)
        return option

    def delete_option(self, option: Option) -> None:
        """선택지 삭제"""
        self.db.delete(option)
        # commit은 Service에서 수행
