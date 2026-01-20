from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.event import EventService
from app.services.event.membership_service import MembershipService
from app.services.event.proposal import ProposalService
from app.services.event.comment_service import CommentService
from app.services.event.setting_service import EventSettingService
from app.services.event.vote_service import VoteService
from app.services.idempotency_service import IdempotencyService
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.repositories.event_repository import EventRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.content.comment import CommentRepository
from app.repositories.vote_repository import VoteRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.outbox_repository import OutboxRepository
from app.dependencies.repositories import (
    get_event_aggregate_repositories,
    get_membership_repository,
    get_event_repository,
    get_comment_repository,
    get_vote_repository,
    get_idempotency_repository,
    get_outbox_repository,
)


def get_event_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventService:
    """EventService 의존성 주입"""
    return EventService(db=db, repos=repos)


def get_idempotency_service(
    db: Session = Depends(get_db),
    idempotency_repo: IdempotencyRepository = Depends(get_idempotency_repository),
) -> IdempotencyService:
    """IdempotencyService 의존성 주입"""
    return IdempotencyService(db=db, idempotency_repo=idempotency_repo)


def get_membership_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
    outbox_repo: OutboxRepository = Depends(get_outbox_repository),
) -> MembershipService:
    """MembershipService 의존성 주입"""
    return MembershipService(
        db=db,
        repos=repos,
        membership_repo=membership_repo,
        event_repo=event_repo,
        idempotency_service=idempotency_service,
        outbox_repo=outbox_repo
    )


def get_proposal_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
    outbox_repo: OutboxRepository = Depends(get_outbox_repository),
) -> ProposalService:
    """ProposalService 의존성 주입"""
    return ProposalService(
        db=db,
        repos=repos,
        idempotency_service=idempotency_service,
        outbox_repo=outbox_repo
    )


def get_comment_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> CommentService:
    """CommentService 의존성 주입"""
    return CommentService(db=db, repos=repos, comment_repo=comment_repo)


def get_setting_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventSettingService:
    """EventSettingService 의존성 주입"""
    return EventSettingService(db=db, repos=repos)


def get_vote_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
    vote_repo: VoteRepository = Depends(get_vote_repository),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> VoteService:
    """VoteService 의존성 주입"""
    return VoteService(db=db, repos=repos, vote_repo=vote_repo, idempotency_service=idempotency_service)
