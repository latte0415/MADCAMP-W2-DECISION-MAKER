from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.event import Event


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: Event) -> Event:
        """이벤트 생성"""
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def exists_by_entrance_code(self, entrance_code: str) -> bool:
        """입장 코드 중복 확인"""
        stmt = select(Event).where(Event.entrance_code == entrance_code)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
