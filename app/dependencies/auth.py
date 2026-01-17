from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.repositories.auth import UserRepository


# Reads: Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """UserRepository 의존성 주입"""
    return UserRepository(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Return the authenticated User ORM object.

    - Extracts Bearer token from Authorization header
    - Verifies JWT signature/expiry/type='access'
    - Loads user from DB
    """
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
