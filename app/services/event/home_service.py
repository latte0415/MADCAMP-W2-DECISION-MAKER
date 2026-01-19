from typing import List
from uuid import UUID

from app.services.event.base import EventBaseService
from app.schemas.event import EventListItemResponse


class EventHomeService(EventBaseService):
    """Home (3-0-0) 관련 서비스"""
    
    def get_events_participated(self, user_id: UUID) -> List[EventListItemResponse]:
        """사용자가 참가한 이벤트 목록 조회 (최적화 버전)"""
        events = self.repos.event.get_events_by_user_id(user_id)
        
        if not events:
            return []
        
        # 모든 이벤트 ID 수집
        event_ids = [event.id for event in events]
        
        # 한 번의 쿼리로 모든 참가 인원 수 조회
        participant_counts = self.repos.event.get_participant_counts_by_event_ids(event_ids)
        
        # 한 번의 쿼리로 모든 멤버십 상태 조회
        membership_statuses = self.repos.event.get_membership_statuses_by_event_ids(user_id, event_ids)
        
        # 최적화 버전: 메모리에서 매핑
        result = []
        for event in events:
            # 참가 인원 카운트 (딕셔너리에서 조회, 없으면 0)
            participant_count = participant_counts.get(event.id, 0)
            
            # 멤버십 상태 (딕셔너리에서 조회, 없으면 None)
            membership_status = membership_statuses.get(event.id)
            
            # 관리자 여부 확인
            is_admin = event.admin_id == user_id
            
            # 관리자 이름 (email 사용, User 모델에 name이 없으므로)
            admin_name = event.admin.email if event.admin else None
            
            result.append(
                EventListItemResponse(
                    id=event.id,
                    decision_subject=event.decision_subject,
                    event_status=event.event_status,
                    admin_id=event.admin_id,
                    admin_name=admin_name,
                    entrance_code=event.entrance_code,
                    participant_count=participant_count,
                    is_admin=is_admin,
                    membership_status=membership_status,
                )
            )
        
        return result
