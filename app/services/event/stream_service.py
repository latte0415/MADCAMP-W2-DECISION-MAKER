from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.outbox_repository import OutboxRepository
from app.models.outbox import OutboxEvent
from app.schemas.event.stream import EventUpdateResponse


class EventStreamService:
    """SSE 스트림 서비스"""
    
    def __init__(self, db: Session, outbox_repo: OutboxRepository):
        self.db = db
        self.outbox_repo = outbox_repo
    
    def get_event_updates(
        self,
        target_event_id: UUID,
        last_id: Optional[UUID] = None,
        limit: int = 100
    ) -> tuple[list[EventUpdateResponse], Optional[UUID]]:
        """
        이벤트 업데이트 조회 (ID 기반 커서)
        
        Args:
            target_event_id: 대상 이벤트 ID
            last_id: 마지막으로 처리한 Outbox 이벤트 ID (커서)
            limit: 최대 조회 개수
        
        Returns:
            (events, last_id): (이벤트 목록, 마지막 이벤트 ID)
        """
        events = self.outbox_repo.get_events_for_sse(
            target_event_id=target_event_id,
            last_id=last_id,
            limit=limit
        )
        
        # Outbox 이벤트를 SSE 응답 형식으로 변환
        event_responses = [
            EventUpdateResponse(
                id=event.id,
                event_type=event.event_type,
                payload=event.payload,
                created_at=event.created_at
            )
            for event in events
        ]
        
        # 마지막 이벤트 ID 계산
        last_event_id = events[-1].id if events else last_id
        
        return event_responses, last_event_id
    
    @staticmethod
    def format_sse_message(event_id: UUID, data: dict) -> str:
        """
        SSE 메시지 형식으로 변환
        
        Args:
            event_id: 이벤트 ID (Last-Event-ID용)
            data: 이벤트 데이터
        
        Returns:
            SSE 형식 문자열: "id: <event_id>\ndata: {...}\n\n"
        """
        import json
        return f"id: {event_id}\ndata: {json.dumps(data, default=str)}\n\n"
    
    @staticmethod
    def format_heartbeat() -> str:
        """
        Heartbeat 메시지 생성
        
        Returns:
            SSE 형식 heartbeat: ": ping\n\n"
        """
        return ": ping\n\n"
    
    @staticmethod
    def format_retry(retry_ms: int = 5000) -> str:
        """
        Retry 헤더 생성
        
        Args:
            retry_ms: 재시도 간격 (밀리초)
        
        Returns:
            SSE 형식 retry: "retry: <retry_ms>\n\n"
        """
        return f"retry: {retry_ms}\n\n"
