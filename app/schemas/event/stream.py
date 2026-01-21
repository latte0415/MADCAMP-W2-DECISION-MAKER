from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class EventUpdateResponse(BaseModel):
    """SSE 응답 스키마"""
    id: UUID = Field(..., description="Outbox 이벤트 ID (Last-Event-ID용)")
    event_type: str = Field(..., description="Outbox 이벤트 타입")
    payload: dict = Field(..., description="Outbox payload (최소화된 형태)")
    created_at: datetime = Field(..., description="이벤트 발생 시각")
