# app/services/auth.py

from __future__ import annotations

import os
from datetime import timedelta
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.auth import (
    RefreshTokenRepository,
    PasswordResetTokenRepository,
    UserIdentityRepository,
    UserRepository,
    UniqueViolation,
)
from app.schemas.auth import CurrentUser
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    hash_password_reset_token,
    hash_password,
    hash_refresh_token,
    utcnow,
    verify_password,
    verify_token,
)
from app.utils.google_auth import GoogleAuthError, verify_google_id_token
from app.utils.mailer import MailerError, SendGridMailer

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

class InvalidGoogleToken(AuthServiceError):
    pass

class LocalLoginNotAvailable(AuthServiceError):
    '''
    A linked google account exists for the given email, but not a local one.
    '''
    def __init__(self, provider: str = "google"):
        self.provider = provider

class UserNotFound(AuthServiceError):
    pass

class InvalidPasswordResetToken(AuthServiceError):
    pass

class PasswordResetEmailSendFailed(AuthServiceError):
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
        reset_repo: PasswordResetTokenRepository,
        mailer: SendGridMailer,
    ):
        self.db = db
        self.user_repo = user_repo
        self.identity_repo = identity_repo
        self.token_repo = token_repo
        self.reset_repo = reset_repo
        self.mailer = mailer
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
    
    def _password_reset_ttl(self) -> timedelta:
        minutes = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30"))
        return timedelta(minutes=minutes)

    def _build_password_reset_link(self, raw_token: str) -> str:
        """
        Frontend URL should be something like: https://.../reset-password
        """
        base = os.getenv("FRONTEND_BASE_URL", "").strip().rstrip("/")
        if not base:
            raise RuntimeError("FRONTEND_BASE_URL is not set")
        return f"{base}/reset-password?token={raw_token}"

    # -------------------------
    # Public service methods
    # -------------------------

    def signup(self, *, email: str, password: str) -> AuthResult:
        """
        - Enforce unique local identity per email
        - Create user + local identity within a transaction
        - Issue tokens and persist refresh token hash
        """

        pw_hash = hash_password(password)

        with self.db.begin():
                    # Fast-fail check (still keep DB constraints as ultimate guard)
            if self.user_repo.get_by_email(email):
                raise EmailAlreadyExists()

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

        with self.db.begin():
            user = self.user_repo.get_by_email(email)
            if not user:
                raise InvalidCredentials()

            if not user.is_active:
                raise InactiveUser()
            
            if not user.password_hash: # this can only happen if the user logged in with google and did not set the password via reset.
                raise LocalLoginNotAvailable(provider="google")

            if not verify_password(password, user.password_hash):
                raise InvalidCredentials()
            
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
    
    def login_google(self, *, id_token: str) -> AuthResult:
        """
        Minimal Google login:
        - Verify Google ID token server-side
        - Lookup by (provider="google", provider_user_id=sub)
        - If missing, link by email if existing user with same email exists
        - Else create new user (password_hash=None)
        - Create google identity row
        - Issue our tokens + store refresh hash
        """
        try:
            info = verify_google_id_token(id_token)
        except GoogleAuthError as e:
            raise InvalidGoogleToken() from e

        google_sub = info.sub
        email = info.email  # may be None depending on scopes/settings

        with self.db.begin():
            # 1) If identity exists already, use it
            identity = self.identity_repo.get_by_provider_user_id_with_user(
                provider="google",
                provider_user_id=google_sub,
            )
            user = None
            if identity:
                user = self.user_repo.get_by_id(identity.user_id)

            # 2) Else link by email (collision handling) or create user
            if user is None:
                if email:
                    existing_user = self.user_repo.get_by_email(email)
                else:
                    existing_user = None

                if existing_user:
                    user = existing_user
                else:
                    # Create new OAuth-first user; no local password.
                    try:
                        user = self.user_repo.create(email=email, password_hash=None)
                    except UniqueViolation:
                        # Extremely unlikely here, but if email got created concurrently, retry by email lookup.
                        if email:
                            user = self.user_repo.get_by_email(email)
                        if user is None:
                            raise

                # Create Google identity for this user
                try:
                    self.identity_repo.create(
                        user_id=user.id,
                        provider="google",
                        provider_user_id=google_sub,
                        email=email,
                    )
                except UniqueViolation:
                    # If another request created the identity concurrently, proceed (idempotent-ish)
                    pass

            if not user.is_active:
                raise InactiveUser()

            access, refresh, refresh_expires_at = self._issue_tokens_for_user(
                user_id=user.id,
                email=user.email or email,
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

    def request_password_reset(self, *, email: str) -> None:
        """
        Class-project policy: if user does not exist -> raise UserNotFound.
        If exists:
          - invalidate previous unused reset tokens for that user
          - create new reset token row (store hash + expiry)
          - send email via SendGrid with reset link
        """
        now = utcnow()

        
        with self.db.begin():
            # 1) Find user (outside transaction is fine)
            user = self.user_repo.get_by_email(email)
            if not user:
                raise UserNotFound()
            if not user.is_active:
                raise InactiveUser()

            # 2) Create token + persist DB row
            raw = create_password_reset_token()
            token_hash = hash_password_reset_token(raw)
            expires_at = now + self._password_reset_ttl()

            # latest-only semantics
            self.reset_repo.invalidate_all_for_user(user_id=user.id, used_at=now)
            self.reset_repo.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)

        # 3) Send email after commit (avoid keeping TX open)
        link = self._build_password_reset_link(raw)
        try:
            self.mailer.send_password_reset_email(to_email=email, reset_link=link)
        except MailerError as e:
            raise PasswordResetEmailSendFailed() from e
        
    def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        """
        Validate token (exists, unused, not expired), set new password hash,
        mark token used, and revoke all refresh tokens for user.
        """
        now = utcnow()
        token_hash = hash_password_reset_token(token)

        with self.db.begin():
            prt = self.reset_repo.get_active_by_hash(token_hash=token_hash, now=now)
            if not prt:
                raise InvalidPasswordResetToken()

            user = self.user_repo.get_by_id(prt.user_id)
            if not user or not user.is_active:
                raise InvalidPasswordResetToken()

            # Update password
            pw_hash = hash_password(new_password)
            updated = self.user_repo.set_password_hash(user_id=user.id, password_hash=pw_hash)
            if updated != 1:
                raise InvalidPasswordResetToken()

            # Consume token (one-time use)
            self.reset_repo.mark_used_by_hash(token_hash=token_hash, used_at=now)

            # Invalidate sessions (important with refresh-cookie auth)
            self.token_repo.revoke_all_for_user(user_id=user.id, revoked_at=now)

    def update_name(self, *, user_id: UUID, name: str) -> None:
        """
        Update user's name.
        """
        updated = self.user_repo.set_name(user_id=user_id, name=name)
        if updated != 1:
            raise UserNotFound()
        self.db.flush()
        self.db.commit()
