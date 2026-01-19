from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.event import EventService
from app.services.event.membership_service import MembershipService
from app.services.event.proposal_service import ProposalService
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.repositories.event_repository import EventRepository
from app.repositories.membership_repository import MembershipRepository
from app.dependencies.repositories import (
    get_event_aggregate_repositories,
    get_membership_repository,
    get_event_repository,
)


def get_event_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventService:
    """EventService 의존성 주입"""
    return EventService(db=db, repos=repos)


def get_membership_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
    event_repo: EventRepository = Depends(get_event_repository),
) -> MembershipService:
    """MembershipService 의존성 주입"""
    return MembershipService(
        db=db,
        repos=repos,
        membership_repo=membership_repo,
        event_repo=event_repo
    )


def get_proposal_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> ProposalService:
    """ProposalService 의존성 주입"""
    return ProposalService(db=db, repos=repos)
