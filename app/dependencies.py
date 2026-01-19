from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.repositories.auth import RefreshTokenRepository, UserIdentityRepository, UserRepository, PasswordResetTokenRepository
from app.services.auth import AuthService
from app.utils.mailer import SendGridMailer, build_sendgrid_mailer_from_env
from app.utils.security import verify_token

# Reads: Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------
# Repository dependencies
# ---------------------------------------------------------------------

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_identity_repository(db: Session = Depends(get_db)) -> UserIdentityRepository:
    return UserIdentityRepository(db)


def get_refresh_token_repository(db: Session = Depends(get_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)

def get_password_reset_token_repository(db: Session = Depends(get_db)) -> PasswordResetTokenRepository:
    return PasswordResetTokenRepository(db)

# ---------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------

def get_mailer() -> SendGridMailer:
    # Reads SENDGRID_API_KEY and SENDGRID_FROM_EMAIL from env
    return build_sendgrid_mailer_from_env()


def get_auth_service(
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    identity_repo: UserIdentityRepository = Depends(get_user_identity_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    reset_repo: PasswordResetTokenRepository = Depends(get_password_reset_token_repository),
    mailer: SendGridMailer = Depends(get_mailer),
) -> AuthService:
    return AuthService(
        db=db,
        user_repo=user_repo,
        identity_repo=identity_repo,
        token_repo=token_repo,
        reset_repo=reset_repo,
        mailer=mailer,
    )

# ---------------------------------------------------------------------
# Auth dependency: current user from access token
# ---------------------------------------------------------------------

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
