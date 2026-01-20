import uuid
from fastapi import Depends, HTTPException, status, Header
from os import getenv


def is_development() -> bool:
    """개발 환경인지 확인"""
    env = getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local")


def get_idempotency_key(
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
) -> str:
    """
    Idempotency-Key 헤더 검증
    - 개발 환경: 헤더가 없으면 자동으로 UUID 생성
    - 운영 환경: 헤더가 없으면 400 에러 반환
    - 헤더 값 반환
    """
    if idempotency_key:
        return idempotency_key
    
    # 개발 환경에서는 자동 생성
    if is_development():
        return str(uuid.uuid4())
    
    # 운영 환경에서는 필수
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Idempotency-Key header is required"
    )
