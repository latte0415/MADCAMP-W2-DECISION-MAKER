from __future__ import annotations

import hashlib
import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Mapping, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# ---------------------------------------------------------------------
# Password hashing (bcrypt via passlib)
# ---------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    """
    Hash a raw password using bcrypt.
    Returns a passlib-formatted hash string.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a raw password against the stored hash.
    Returns True if matches; otherwise False.
    """
    if not password or not password_hash:
        return False
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        # If the stored hash is malformed or uses an unsupported scheme, treat as non-match.
        return False


# ---------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------

def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def compute_expires_at(expires_delta: timedelta) -> datetime:
    """Compute an absolute UTC datetime expiration timestamp."""
    if not isinstance(expires_delta, timedelta):
        raise ValueError("expires_delta must be a timedelta")
    return utcnow() + expires_delta


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------

def _load_jwt_settings() -> tuple[str, str]:
    """
    Load SECRET_KEY and ALGORITHM from environment variables.
    """
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    if not secret_key or len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY environment variable is not set (or too short; use 32+ chars)")

    return secret_key, algorithm


def _access_token_default_ttl() -> timedelta:
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    return timedelta(minutes=minutes)


def _refresh_token_default_ttl() -> timedelta:
    days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    return timedelta(days=days)


def create_access_token(
    *,
    subject: str,  # typically user_id (uuid as str)
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Create a signed JWT access token.

    Includes:
      - sub: subject (user id)
      - type: "access"
      - iat, exp: epoch seconds
      - email (optional)
      - extra_claims (optional, cannot overwrite reserved claims)
    """
    secret_key, algorithm = _load_jwt_settings()

    if not subject or not isinstance(subject, str):
        raise ValueError("subject must be a non-empty string")

    now = utcnow()
    expire = now + (expires_delta or _access_token_default_ttl())

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if email is not None:
        payload["email"] = email

    if extra_claims:
        for k, v in extra_claims.items():
            if k in {"sub", "type", "iat", "exp"}:
                raise ValueError(f"extra_claims must not override reserved claim: {k}")
            payload[k] = v

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    *,
    subject: str,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
    extra_claims: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Create a signed JWT refresh token.

    Includes:
      - sub: subject (user id)
      - type: "refresh"
      - jti: token unique id (auto-generated if not provided)
      - iat, exp
      - extra_claims (optional, cannot overwrite reserved claims)
    """
    secret_key, algorithm = _load_jwt_settings()

    if not subject or not isinstance(subject, str):
        raise ValueError("subject must be a non-empty string")

    now = utcnow()
    expire = now + (expires_delta or _refresh_token_default_ttl())

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "jti": jti or str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if extra_claims:
        for k, v in extra_claims.items():
            if k in {"sub", "type", "iat", "exp", "jti"}:
                raise ValueError(f"extra_claims must not override reserved claim: {k}")
            payload[k] = v

    return jwt.encode(payload, secret_key, algorithm=algorithm)

def create_password_reset_token(*, nbytes: int = 32) -> str:
    """
    Create a URL-safe password reset token suitable for including in a link.
    Uses cryptographically secure randomness (os.urandom).
    """
    if not isinstance(nbytes, int) or nbytes < 16:
        raise ValueError("nbytes must be an int >= 16")
    raw = os.urandom(nbytes)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def verify_token(
    token: str,
    *,
    expected_type: Optional[TokenType] = None,
) -> Dict[str, Any]:
    """
    Verify a JWT and return its decoded payload.

    Verifies:
      - signature validity
      - exp (expiry) validity (python-jose enforces exp by default)
      - required claims: sub, type
      - if expected_type provided: payload['type'] must match

    Does NOT:
      - check DB state (revocation, rotation, token_hash existence)
    """
    secret_key, algorithm = _load_jwt_settings()

    if not token or not isinstance(token, str):
        raise ValueError("token must be a non-empty string")

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as e:
        raise ValueError("Invalid token") from e

    sub = payload.get("sub")
    token_type = payload.get("type")

    if not sub or not isinstance(sub, str):
        raise ValueError("Invalid token: missing/invalid 'sub'")

    if token_type not in ("access", "refresh"):
        raise ValueError("Invalid token: missing/invalid 'type'")

    if expected_type is not None and token_type != expected_type:
        raise ValueError(f"Invalid token type: expected '{expected_type}', got '{token_type}'")

    return payload


# ---------------------------------------------------------------------
# token hashing for DB storage (deterministic)
# ---------------------------------------------------------------------

def hash_refresh_token(token: str) -> str:
    """
    Deterministically hash the refresh token for DB storage.
    Use this when writing/looking up refresh_tokens.token_hash.
    """
    if not token or not isinstance(token, str):
        raise ValueError("token must be a non-empty string")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def hash_password_reset_token(token: str) -> str:
    """
    Deterministically hash the password reset token for DB storage.
    Use this when writing/looking up password_reset_tokens.token_hash.
    """
    if not token or not isinstance(token, str):
        raise ValueError("token must be a non-empty string")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()