from sqlalchemy import select, update
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from uuid import UUID
import os
import socket

from app.models.outbox import OutboxEvent, OutboxStatusType


class OutboxRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_outbox_event(
        self,
        event_type: str,
        payload: dict,
        target_event_id: UUID,
        next_retry_at: datetime | None = None
    ) -> OutboxEvent:
        """트랜잭션 내에서 outbox 이벤트 저장"""
        if next_retry_at is None:
            next_retry_at = datetime.now(timezone.utc)
        
        event = OutboxEvent(
            event_type=event_type,
            payload=payload,
            target_event_id=target_event_id,
            status=OutboxStatusType.PENDING,
            attempts=0,
            next_retry_at=next_retry_at
        )
        self.db.add(event)
        self.db.flush()
        return event
    
    def claim_pending_events(
        self,
        batch_size: int,
        worker_id: str,
        now: datetime,
        lock_ttl_minutes: int = 5
    ) -> list[OutboxEvent]:
        """
        워커 선점 패턴: FOR UPDATE SKIP LOCKED 사용
        
        핵심 흐름:
        1. 트랜잭션 시작 (호출자가 관리)
        2. PENDING이고 next_retry_at <= now인 row를
           FOR UPDATE SKIP LOCKED로 batch 조회
        3. 조회된 row들을 즉시 locked_at/locked_by 갱신(선점)
        4. 트랜잭션 커밋 (호출자가 관리)
        5. 커밋 후 실제 핸들러 실행 (트랜잭션 외부)
        
        수정사항:
        - 락 TTL 회수 로직 추가 (locked_at이 오래된 경우 재선점 가능)
        - 반환 전 refresh로 락 상태 동기화
        """
        # 락 TTL 계산: 오래된 락은 회수 대상
        lock_ttl_threshold = now - timedelta(minutes=lock_ttl_minutes)
        
        # 1. FOR UPDATE SKIP LOCKED로 선점 가능한 이벤트 조회
        # 수정: 락 TTL 회수 조건 추가 (locked_at is null OR locked_at < threshold)
        stmt = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status == OutboxStatusType.PENDING,
                OutboxEvent.next_retry_at <= now,
                # 락이 없거나, 락이 TTL을 초과한 경우만 선점 가능
                (
                    (OutboxEvent.locked_at.is_(None)) |
                    (OutboxEvent.locked_at < lock_ttl_threshold)
                )
            )
            .order_by(OutboxEvent.created_at)  # FIFO
            .limit(batch_size)
            .with_for_update(skip_locked=True)  # 핵심: 다른 워커가 잠근 row는 건너뜀
        )
        result = self.db.execute(stmt)
        events = result.scalars().all()
        
        if not events:
            return []
        
        # 2. 조회된 이벤트들을 즉시 선점 표시
        event_ids = [event.id for event in events]
        update_stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id.in_(event_ids))
            .values(
                locked_at=now,
                locked_by=worker_id
            )
        )
        self.db.execute(update_stmt)
        self.db.flush()
        
        # 3. 수정: 반환 전 각 이벤트를 refresh하여 락 상태 동기화
        for event in events:
            self.db.refresh(event)
        
        return events
    
    def mark_done(self, event_id: UUID, processed_at: datetime) -> None:
        """처리 완료 표시"""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxStatusType.DONE,
                processed_at=processed_at,
                locked_at=None,
                locked_by=None
            )
        )
        self.db.execute(stmt)
        self.db.flush()
    
    def mark_failed(
        self,
        event_id: UUID,
        error: str,
        next_retry_at: datetime,
        max_attempts: int = 3
    ) -> bool:
        """
        실패 표시 및 재시도 스케줄링
        
        수정: 원자성 보장 - DB에서 attempts를 직접 증가시켜 경쟁 상황 안전
        
        Returns:
            True: 재시도 가능, False: 최대 시도 횟수 초과 (FAILED 상태로 전환)
        """
        # 수정: 원자적으로 attempts를 증가시키고 그 값을 RETURNING으로 받기
        # 이렇게 하면 여러 워커가 동시에 시도해도 안전함
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                attempts=OutboxEvent.attempts + 1  # DB에서 직접 증가
            )
            .returning(OutboxEvent.attempts)  # 증가된 attempts 값 반환
        )
        result = self.db.execute(stmt)
        new_attempts = result.scalar_one_or_none()
        
        if new_attempts is None:
            # 이벤트가 존재하지 않음
            return False
        
        if new_attempts >= max_attempts:
            # 최대 시도 횟수 초과 → FAILED 상태로 전환 (DLQ)
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.id == event_id)
                .values(
                    status=OutboxStatusType.FAILED,
                    last_error=error,
                    locked_at=None,
                    locked_by=None
                )
            )
            self.db.execute(stmt)
            self.db.flush()
            return False
        else:
            # 재시도 가능 → next_retry_at 업데이트
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.id == event_id)
                .values(
                    next_retry_at=next_retry_at,
                    last_error=error,
                    locked_at=None,
                    locked_by=None,
                    status=OutboxStatusType.PENDING  # 다시 PENDING으로
                )
            )
            self.db.execute(stmt)
            self.db.flush()
            return True


    def get_events_for_sse(
        self,
        target_event_id: UUID,
        last_id: UUID | None,
        limit: int = 100
    ) -> list[OutboxEvent]:
        """
        SSE 전용 읽기 메서드 (읽기 전용, DONE 표시하지 않음)
        
        ID 기반 커서를 사용하여 누락/중복 방지
        Worker 처리 상태(status)와 무관하게 모든 이벤트 조회
        """
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.target_event_id == target_event_id)
            .order_by(OutboxEvent.id.asc())
            .limit(limit)
        )
        
        if last_id:
            stmt = stmt.where(OutboxEvent.id > last_id)
        
        result = self.db.execute(stmt)
        return list(result.scalars().all())


def get_worker_id() -> str:
    """워커 식별자 생성 (hostname:pid)"""
    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}:{pid}"
