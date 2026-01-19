"""
Dependencies module - 재export를 통해 기존 코드와의 호환성 유지
"""
from __future__ import annotations

# Auth 관련 - auth.py에서 재export
from app.dependencies.auth import (
    get_current_user,
    get_user_repository,
    get_user_identity_repository,
    get_refresh_token_repository,
    get_password_reset_token_repository,
    get_auth_service,
    get_mailer,
)

# Event 관련
from app.dependencies.repositories import get_event_repository
from app.dependencies.services import get_event_service

__all__ = [
    "get_current_user",
    "get_user_repository",
    "get_user_identity_repository",
    "get_refresh_token_repository",
    "get_password_reset_token_repository",
    "get_auth_service",
    "get_mailer",
    "get_event_repository",
    "get_event_service",
]
