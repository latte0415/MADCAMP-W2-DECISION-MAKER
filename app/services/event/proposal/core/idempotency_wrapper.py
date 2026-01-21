"""Idempotency 명시적 래핑"""
from typing import Callable
from uuid import UUID

from app.services.idempotency_service import IdempotencyService


class IdempotencyWrapper:
    """Idempotency 명시적 래핑 헬퍼"""
    
    def __init__(self, idempotency_service: IdempotencyService | None):
        self.idempotency_service = idempotency_service
    
    def wrap(
        self,
        idempotency_key: str | None,
        user_id: UUID,
        method: str,
        path: str,
        body: dict,
        fn: Callable[[], dict],
    ) -> dict:
        """
        Idempotency 래핑
        
        Args:
            idempotency_key: Idempotency 키 (None이면 래핑하지 않음)
            user_id: 사용자 ID
            method: HTTP 메서드
            path: HTTP 경로
            body: 요청 본문
            fn: 실행할 함수
        """
        if self.idempotency_service and idempotency_key:
            return self.idempotency_service.run(
                user_id=user_id,
                key=idempotency_key,
                method=method,
                path=path,
                body=body,
                fn=fn
            )
        else:
            return fn()
