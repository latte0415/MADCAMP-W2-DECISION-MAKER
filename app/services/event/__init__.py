"""
Event 관련 서비스 모듈
기존 코드 호환성을 위한 통합 Service 클래스 제공
"""
from sqlalchemy.orm import Session

from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.services.event.base import EventBaseService
from app.services.event.home_service import EventHomeService
from app.services.event.creation_service import EventCreationService
from app.services.event.overview_service import EventOverviewService
from app.services.event.detail_service import EventDetailService
from app.services.event.setting_service import EventSettingService


# 모든 Service 클래스 export
__all__ = [
    "EventBaseService",
    "EventHomeService",
    "EventCreationService",
    "EventOverviewService",
    "EventDetailService",
    "EventSettingService",
    "EventService",  # 통합 클래스
]


class EventService(EventBaseService):
    """
    통합 EventService 클래스 (기존 코드 호환성)
    내부에서 기능별 Service를 조합하여 사용
    """
    
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        super().__init__(db, repos)
        # 기능별 Service 인스턴스 생성
        self._home_service = EventHomeService(db, repos)
        self._creation_service = EventCreationService(db, repos)
        self._overview_service = EventOverviewService(db, repos)
        self._detail_service = EventDetailService(db, repos)
        self._setting_service = EventSettingService(db, repos)
    
    # Home 관련 메서드
    def get_events_participated(self, user_id):
        return self._home_service.get_events_participated(user_id)
    
    # Creation 관련 메서드
    def create_event(self, request, admin_id):
        return self._creation_service.create_event(request, admin_id)
    
    def attach_options(self, event_id, option_requests, created_by):
        return self._creation_service.attach_options(event_id, option_requests, created_by)
    
    def attach_assumptions(self, event_id, assumption_requests, created_by):
        return self._creation_service.attach_assumptions(event_id, assumption_requests, created_by)
    
    def attach_criteria(self, event_id, criterion_requests, created_by):
        return self._creation_service.attach_criteria(event_id, criterion_requests, created_by)
    
    def check_entrance_code_availability(self, entrance_code):
        return self._creation_service.check_entrance_code_availability(entrance_code)
    
    def get_random_code(self):
        return self._creation_service.get_random_code()
    
    # Overview 관련 메서드
    def get_event_overview(self, event_id, user_id):
        return self._overview_service.get_event_overview(event_id, user_id)
    
    # Detail 관련 메서드
    def get_event_detail(self, event_id, user_id):
        return self._detail_service.get_event_detail(event_id, user_id)
    
    # Setting 관련 메서드
    def get_event_setting(self, event_id, user_id):
        return self._setting_service.get_event_setting(event_id, user_id)
    
    def update_event(self, event_id, request, user_id):
        return self._setting_service.update_event(event_id, request, user_id)
