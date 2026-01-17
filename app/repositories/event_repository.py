from sqlalchemy.orm import Session

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
