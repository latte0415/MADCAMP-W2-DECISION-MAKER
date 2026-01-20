from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.idempotency import IdempotencyRecord, IdempotencyStatusType


class IdempotencyRepository:
    """Idempotency 레코드 관리 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def try_acquire(
        self,
        user_id: UUID,
        key: str,
        method: str,
        path: str,
        request_hash: str,
        ttl: timedelta
    ) -> Optional[IdempotencyRecord]:
        """
        키 선점 시도
        - UNIQUE 충돌 시 rollback 후 None 반환
        - 성공 시 IN_PROGRESS 상태의 레코드 생성 및 반환
        """
        from datetime import timezone
        expires_at = datetime.now(timezone.utc) + ttl
        
        record = IdempotencyRecord(
            user_id=user_id,
            key=key,
            method=method,
            path=path,
            request_hash=request_hash,
            status=IdempotencyStatusType.IN_PROGRESS,
            expires_at=expires_at
        )
        
        try:
            self.db.add(record)
            self.db.flush()
            self.db.refresh(record)
            return record
        except IntegrityError:
            # UNIQUE 충돌 발생 시 rollback
            self.db.rollback()
            return None
    
    def get(
        self,
        user_id: UUID,
        key: str
    ) -> Optional[IdempotencyRecord]:
        """레코드 조회"""
        stmt = (
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.key == key
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def mark_completed(
        self,
        record: IdempotencyRecord,
        response_code: int,
        response_body: dict
    ) -> IdempotencyRecord:
        """성공 응답 저장"""
        record.status = IdempotencyStatusType.COMPLETED
        record.response_code = response_code
        record.response_body = response_body
        self.db.flush()
        self.db.refresh(record)
        return record
    
    def mark_failed(
        self,
        record: IdempotencyRecord
    ) -> IdempotencyRecord:
        """실패 처리"""
        record.status = IdempotencyStatusType.FAILED
        self.db.flush()
        self.db.refresh(record)
        return record
