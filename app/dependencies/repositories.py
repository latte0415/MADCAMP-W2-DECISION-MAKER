from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.repositories.event_repository import EventRepository
from app.repositories.content.option import OptionRepository
from app.repositories.content.assumption import AssumptionRepository
from app.repositories.content.criterion import CriterionRepository
from app.repositories.membership_repository import MembershipRepository


# Aggregate 의존성
def get_event_aggregate_repositories(db: Session = Depends(get_db)) -> EventAggregateRepositories:
    """Event 관련 Repository들의 Aggregate 의존성 주입"""
    return EventAggregateRepositories(db)


# 개별 Repository 의존성
def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    """EventRepository 의존성 주입"""
    return EventRepository(db)


def get_option_repository(db: Session = Depends(get_db)) -> OptionRepository:
    """OptionRepository 의존성 주입"""
    return OptionRepository(db)


def get_assumption_repository(db: Session = Depends(get_db)) -> AssumptionRepository:
    """AssumptionRepository 의존성 주입"""
    return AssumptionRepository(db)


def get_criterion_repository(db: Session = Depends(get_db)) -> CriterionRepository:
    """CriterionRepository 의존성 주입"""
    return CriterionRepository(db)


def get_membership_repository(db: Session = Depends(get_db)) -> MembershipRepository:
    """MembershipRepository 의존성 주입"""
    return MembershipRepository(db)
