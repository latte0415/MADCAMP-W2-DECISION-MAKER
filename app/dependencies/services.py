from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.event_service import EventService
from app.services.membership_service import MembershipService
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.repositories.membership_repository import MembershipRepository
from app.dependencies.repositories import (
    get_event_aggregate_repositories,
    get_membership_repository,
)


def get_event_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventService:
    """EventService 의존성 주입"""
    return EventService(db=db, repos=repos)


def get_membership_service(
    db: Session = Depends(get_db),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
) -> MembershipService:
    """MembershipService 의존성 주입"""
    return MembershipService(db=db, membership_repo=membership_repo)
