"""
Dependencies module - 재export를 통해 기존 코드와의 호환성 유지
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.auth import RefreshTokenRepository, UserIdentityRepository, UserRepository
from app.services.auth import AuthService

# Event 관련
from app.dependencies.repositories import get_event_repository
from app.dependencies.services import get_event_service

# Auth 관련 - auth.py에서 가져오거나 여기서 정의
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_identity_repository(db: Session = Depends(get_db)) -> UserIdentityRepository:
    return UserIdentityRepository(db)


def get_refresh_token_repository(db: Session = Depends(get_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_auth_service(
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    identity_repo: UserIdentityRepository = Depends(get_user_identity_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(db=db, user_repo=user_repo, identity_repo=identity_repo, token_repo=token_repo)


# get_current_user는 auth.py에서 재export
from app.dependencies.auth import get_current_user

__all__ = [
    "get_current_user",
    "get_user_repository",
    "get_user_identity_repository",
    "get_refresh_token_repository",
    "get_auth_service",
    "get_event_repository",
    "get_event_service",
]
