import uuid
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from sqlalchemy import (
    String, DateTime, ForeignKey, JSON,
    UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IdempotencyStatusType(PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_idempotency_records_user_id_key"),
        Index("idx_idempotency_records_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String, nullable=False)

    # 요청 시그니처
    method: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    request_hash: Mapped[str] = mapped_column(String, nullable=False)

    #상태/응답 저장
    status: Mapped[IdempotencyStatusType] = mapped_column(
        ENUM(IdempotencyStatusType, name="idempotency_status_type", create_type=False),
        nullable=False,
    )
    response_code: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
