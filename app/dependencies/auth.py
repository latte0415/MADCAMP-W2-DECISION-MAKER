from __future__ import annotations

from os import getenv
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.repositories.auth import UserRepository


# Reads: Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)

# 테스트 모드용 사용자 ID 매핑
TEST_USER_IDS = {
    "ADMIN": UUID("23f9e5e2-c42a-4e28-8c88-7df2b4a4fde6"),
    "USER1": UUID("145e7c12-1235-48e1-a1bd-49347106a1ce"),
    "USER2": UUID("e69ff764-f351-440b-a3f3-a7ebc4b4e2e7"),
}


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """UserRepository 의존성 주입"""
    return UserRepository(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Return the authenticated User ORM object.

    - TEST_MODE=TRUE일 때: USER 환경변수(ADMIN/USER1/USER2)로 사용자 선택
    - 일반 모드: JWT 토큰에서 사용자 정보 추출 및 검증
    """
    # 테스트 모드 체크
    test_mode = getenv("TEST_MODE", "").upper() == "TRUE"
    if test_mode:
        test_user = getenv("USER", "").upper()
        # test_user = "USER1"
        if test_user in TEST_USER_IDS:
            user_id = TEST_USER_IDS[test_user]
            user = user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Test user {test_user} not found or inactive",
                )
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid TEST_MODE USER. Must be one of: {', '.join(TEST_USER_IDS.keys())}",
            )
    
    # 일반 모드: JWT 토큰 검증
    from app.utils.security import verify_token
    
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = verify_token(token, expected_type="access")
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise ValueError("missing sub")
        user_id = UUID(sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
