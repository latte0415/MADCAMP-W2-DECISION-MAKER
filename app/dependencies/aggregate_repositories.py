"""
Repository Aggregate 패턴 구현
의존성 주입을 위해 관련 Repository들을 하나로 묶은 Aggregate 클래스들
"""
from sqlalchemy.orm import Session

from app.repositories.event_repository import EventRepository
from app.repositories.option_repository import OptionRepository
from app.repositories.assumption_repository import AssumptionRepository
from app.repositories.criterion_repository import CriterionRepository


class EventAggregateRepositories:
    """Event 관련 모든 Repository를 하나로 묶은 Aggregate"""
    
    def __init__(self, db: Session):
        self.event = EventRepository(db)
        self.option = OptionRepository(db)
        self.assumption = AssumptionRepository(db)
        self.criterion = CriterionRepository(db)
