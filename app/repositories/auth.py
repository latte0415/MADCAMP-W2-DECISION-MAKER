# app/repositories/auth.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import User, UserIdentity, RefreshToken


# ---------------------------------------------------------------------
# Repository exceptions (DB-layer concerns, not HTTP concerns)
# ---------------------------------------------------------------------

class RepositoryError(Exception):
    """Base class for repository-layer errors."""


@dataclass(slots=True)
class UniqueViolation(RepositoryError):
    """
    Raised when a create/insert violates a unique constraint.
    field is a hint for service-level decisions/logging; it is best-effort.
    """
    field: str
    message: str = "Unique constraint violated"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _raise_unique_violation(err: IntegrityError, *, default_field: str) -> None:
    """
    Best-effort mapping of an IntegrityError to a UniqueViolation.
    Postgres error messages vary; keep it simple and robust.
    """
    msg = str(err.orig).lower() if getattr(err, "orig", None) else str(err).lower()

    # Best-effort field inference
    if "users" in msg and "email" in msg:
        raise UniqueViolation(field="email") from err
    if "uq_provider_provider_user_id" in msg or ("provider" in msg and "provider_user_id" in msg):
        raise UniqueViolation(field="provider_user_id") from err
    if "uq_refresh_user_token_hash" in msg or "token_hash" in msg:
        raise UniqueViolation(field="token_hash") from err

    raise UniqueViolation(field=default_field) from err


# ---------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, *, email: str | None, password_hash: str | None) -> User:
        """
        Create a user row. Caller is responsible for transaction scope.
        """
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        try:
            self.db.flush()  # ensures PK is generated
        except IntegrityError as e:
            _raise_unique_violation(e, default_field="user")
        return user

    def set_active(self, *, user_id: UUID, is_active: bool) -> int:
        """
        Returns number of rows updated.
        """
        stmt = update(User).where(User.id == user_id).values(is_active=is_active)
        result = self.db.execute(stmt)
        return len(result.scalars().all())


# ---------------------------------------------------------------------
# UserIdentityRepository
# ---------------------------------------------------------------------

class UserIdentityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_local_by_email(self, email: str) -> Optional[UserIdentity]:
        """
        Lookup local identity by email. Does not eager-load user by default.
        """
        stmt = select(UserIdentity).where(
            UserIdentity.provider == "local",
            UserIdentity.email == email,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_local_by_email_with_user(self, email: str) -> Optional[UserIdentity]:
        """
        Same as get_local_by_email, but eager-loads identity.user in one query.
        Useful for login flow.
        """
        stmt = (
            select(UserIdentity)
            .options(joinedload(UserIdentity.user))
            .where(
                UserIdentity.provider == "local",
                UserIdentity.email == email,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_provider_user_id(self, *, provider: str, provider_user_id: str) -> Optional[UserIdentity]:
        stmt = select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_user_id == provider_user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_by_provider_user_id_with_user(self, *, provider: str, provider_user_id: str) -> Optional[UserIdentity]:
        """
        Eager loading version of above.
        """
        stmt = (
            select(UserIdentity)
            .options(joinedload(UserIdentity.user))
            .where(
                UserIdentity.provider == provider,
                UserIdentity.provider_user_id == provider_user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_local(self, *, user_id: UUID, email: str) -> UserIdentity:
        """
        Create a local identity row.
        Convention: provider_user_id=email (simple and fine for local auth).
        """
        identity = UserIdentity(
            user_id=user_id,
            provider="local",
            provider_user_id=email,
            email=email,
        )
        self.db.add(identity)
        try:
            self.db.flush()
        except IntegrityError as e:
            _raise_unique_violation(e, default_field="identity")
        return identity

    def create(
        self,
        *,
        user_id: UUID,
        provider: str,
        provider_user_id: str,
        email: str | None,
    ) -> UserIdentity:
        """
        Generic identity creator (helps when you later add OAuth).
        """
        identity = UserIdentity(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )
        self.db.add(identity)
        try:
            self.db.flush()
        except IntegrityError as e:
            _raise_unique_violation(e, default_field="identity")
        return identity
    
    def get_by_provider_and_email_with_user(self, *, provider: str, email: str) -> Optional[UserIdentity]:
        stmt = (
            select(UserIdentity)
            .options(joinedload(UserIdentity.user))
            .where(
                UserIdentity.provider == provider,
                UserIdentity.email == email,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()


# ---------------------------------------------------------------------
# RefreshTokenRepository
# ---------------------------------------------------------------------

class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.db.add(rt)
        try:
            self.db.flush()
        except IntegrityError as e:
            _raise_unique_violation(e, default_field="refresh_token")
        return rt

    def get_active_by_hash(self, *, token_hash: str, now: datetime) -> Optional[RefreshToken]:
        """
        Active = (revoked_at IS NULL) AND (expires_at > now)
        """
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_any_by_hash(self, *, token_hash: str) -> Optional[RefreshToken]:
        """
        Fetch regardless of revoked/expired status (useful for audits/debug).
        """
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke_by_hash(self, *, token_hash: str, revoked_at: datetime) -> int:
        """
        Revoke token if it is not already revoked. Returns rows updated.
        """
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.db.execute(stmt)
        return result.rowcount or 0

    def revoke_all_for_user(self, *, user_id: UUID, revoked_at: datetime) -> int:
        """
        Optional: revoke all outstanding refresh tokens for a user.
        """
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.db.execute(stmt)
        return result.rowcount or 0

    def delete_expired_before(self, *, cutoff: datetime) -> int:
        """
        Optional cleanup: delete tokens that expired before cutoff AND are revoked
        (or you can choose to delete all expired). Safe for maintenance jobs.
        """
        stmt = delete(RefreshToken).where(
            RefreshToken.expires_at < cutoff,
            RefreshToken.revoked_at.is_not(None),
        )
        result = self.db.execute(stmt)
        return result.rowcount or 0
