import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    String, DateTime, Integer, Text, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OutboxStatusType(PyEnum):
    PENDING = "PENDING"
    DONE = "DONE"
    FAILED = "FAILED"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("idx_outbox_status_next_retry", "status", "next_retry_at"),  # 필수 인덱스
        Index("idx_outbox_event_type", "event_type"),  # 선택: 모니터링용
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "proposal.approved.v1"
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    status: Mapped[OutboxStatusType] = mapped_column(
        ENUM(OutboxStatusType, name="outbox_status_type", create_type=False),
        nullable=False,
        default=OutboxStatusType.PENDING
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # hostname/pid
    
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
