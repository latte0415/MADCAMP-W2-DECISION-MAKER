# app/services/auth.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.auth import (
    RefreshTokenRepository,
    UserIdentityRepository,
    UserRepository,
    UniqueViolation,
)
from app.schemas.auth import CurrentUser
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    utcnow,
    verify_password,
    verify_token,
)


# ---------------------------------------------------------------------
# Service-level errors (router maps these to HTTP responses)
# ---------------------------------------------------------------------

class AuthServiceError(Exception):
    """Base class for auth service errors."""


class EmailAlreadyExists(AuthServiceError):
    pass


class InvalidCredentials(AuthServiceError):
    pass


class InactiveUser(AuthServiceError):
    pass


class InvalidRefreshToken(AuthServiceError):
    pass


# ---------------------------------------------------------------------
# Return type for service methods (router sets cookie from refresh_token)
# ---------------------------------------------------------------------

@dataclass(slots=True)
class AuthResult:
    access_token: str
    refresh_token: str
    user: CurrentUser


def _exp_to_datetime_utc(exp: int) -> datetime:
    """
    Convert JWT exp (epoch seconds) to timezone-aware UTC datetime for DB expires_at.
    """
    return datetime.fromtimestamp(exp, tz=timezone.utc)


class AuthService:
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository,
        identity_repo: UserIdentityRepository,
        token_repo: RefreshTokenRepository,
    ):
        self.db = db
        self.user_repo = user_repo
        self.identity_repo = identity_repo
        self.token_repo = token_repo

    # -------------------------
    # Core helpers
    # -------------------------

    def _issue_tokens_for_user(self, *, user_id: UUID, email: Optional[str]) -> tuple[str, str, datetime]:
        """
        Create access + refresh tokens, and return refresh expiry for DB.
        """
        access = create_access_token(subject=str(user_id), email=email)
        refresh = create_refresh_token(subject=str(user_id))

        refresh_payload = verify_token(refresh, expected_type="refresh")
        exp = refresh_payload.get("exp")
        if not isinstance(exp, int):
            # Should never happen if create_refresh_token is correct
            raise RuntimeError("Refresh token missing 'exp' claim")

        refresh_expires_at = _exp_to_datetime_utc(exp)
        return access, refresh, refresh_expires_at

    # -------------------------
    # Public service methods
    # -------------------------

    def signup(self, *, email: str, password: str) -> AuthResult:
        """
        - Enforce unique local identity per email
        - Create user + local identity within a transaction
        - Issue tokens and persist refresh token hash
        """
        # Fast-fail check (still keep DB constraints as ultimate guard)
        existing = self.identity_repo.get_local_by_email(email)
        if existing:
            raise EmailAlreadyExists()

        pw_hash = hash_password(password)

        with self.db.begin():
            try:
                user = self.user_repo.create(email=email, password_hash=pw_hash)
                self.identity_repo.create_local(user_id=user.id, email=email)
            except UniqueViolation as e:
                # Covers race conditions (two signups at once) 
                if e.field in ("email", "provider_user_id"):
                    raise EmailAlreadyExists() from e
                raise

            access, refresh, refresh_expires_at = self._issue_tokens_for_user(
                user_id=user.id,
                email=user.email,
            )

            self.token_repo.create(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh),
                expires_at=refresh_expires_at,
            )

        return AuthResult(
            access_token=access,
            refresh_token=refresh,
            user=CurrentUser.model_validate(user),
        )

    def login(self, *, email: str, password: str) -> AuthResult:
        """
        - Find local identity by email
        - Verify password against user's password_hash
        - Issue new tokens and store refresh token hash
        """
        identity = self.identity_repo.get_local_by_email_with_user(email)
        if not identity or not identity.user:
            raise InvalidCredentials()

        user = identity.user

        if not user.is_active:
            raise InactiveUser()

        if not user.password_hash or not verify_password(password, user.password_hash):
            raise InvalidCredentials()

        with self.db.begin():
            access, refresh, refresh_expires_at = self._issue_tokens_for_user(
                user_id=user.id,
                email=user.email,
            )

            self.token_repo.create(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh),
                expires_at=refresh_expires_at,
            )

        return AuthResult(
            access_token=access,
            refresh_token=refresh,
            user=CurrentUser.model_validate(user),
        )

    def refresh(self, *, refresh_token: str) -> AuthResult:
        """
        Refresh token rotation:
        - Verify JWT (signature/exp/type)
        - Hash token and confirm it exists in DB and is active
        - Revoke old token
        - Issue new access+refresh and store new refresh hash
        """
        payload = verify_token(refresh_token, expected_type="refresh")
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise InvalidRefreshToken()

        try:
            user_id = UUID(sub)
        except ValueError:
            raise InvalidRefreshToken()

        token_hash = hash_refresh_token(refresh_token)
        now = utcnow()

        with self.db.begin():
            existing = self.token_repo.get_active_by_hash(token_hash=token_hash, now=now)
            if not existing:
                raise InvalidRefreshToken()

            # revoke old (rotation)
            self.token_repo.revoke_by_hash(token_hash=token_hash, revoked_at=now)

            user = self.user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise InvalidRefreshToken()

            new_access, new_refresh, new_refresh_expires_at = self._issue_tokens_for_user(
                user_id=user.id,
                email=user.email,
            )

            self.token_repo.create(
                user_id=user.id,
                token_hash=hash_refresh_token(new_refresh),
                expires_at=new_refresh_expires_at,
            )

        return AuthResult(
            access_token=new_access,
            refresh_token=new_refresh,
            user=CurrentUser.model_validate(user),
        )

    def logout(self, *, refresh_token: str) -> None:
        """
        Best-effort logout:
        - Hash refresh token and revoke it if present
        - Do not leak whether token existed
        """
        token_hash = hash_refresh_token(refresh_token)
        now = utcnow()
        with self.db.begin():
            self.token_repo.revoke_by_hash(token_hash=token_hash, revoked_at=now)
