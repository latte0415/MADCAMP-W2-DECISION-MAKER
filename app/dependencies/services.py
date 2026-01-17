from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.event_service import EventService
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.dependencies.repositories import get_event_aggregate_repositories


def get_event_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventService:
    """EventService 의존성 주입"""
    return EventService(db=db, repos=repos)
