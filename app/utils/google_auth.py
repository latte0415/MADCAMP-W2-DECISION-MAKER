from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from google.auth.transport.requests import Request
from google.oauth2 import id_token as google_id_token


class GoogleAuthError(ValueError):
    """Raised when Google ID token verification fails."""


@dataclass(frozen=True, slots=True)
class GoogleIdInfo:
    """
    Minimal, useful subset of Google ID token claims for account linking.
    """
    sub: str                      # stable Google user id
    email: Optional[str]          # may be absent depending on scopes/settings
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None


def verify_google_id_token(id_token: str, *, audience: Optional[str] = None) -> GoogleIdInfo:
    """
    Verify Google ID token (JWT) and return selected claims.

    Verifies (server-side):
      - token signature via Google's certs
      - exp not expired
      - iss is a Google issuer
      - aud matches your GOOGLE_CLIENT_ID (audience)
    """
    if not isinstance(id_token, str) or not id_token.strip():
        raise GoogleAuthError("id_token must be a non-empty string")

    client_id = audience or os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")

    try:
        # Fetches/uses Google's certs under the hood as needed.
        # verify_oauth2_token checks issuer; audience is checked when provided.
        claims: Mapping[str, Any] = google_id_token.verify_oauth2_token(
            id_token,
            Request(),
            audience=client_id,
        )
    except Exception as e:
        # keep it generic; do not leak details
        raise GoogleAuthError("Invalid Google ID token") from e

    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise GoogleAuthError("Invalid Google ID token: missing sub")

    email = claims.get("email")
    if email is not None and not isinstance(email, str):
        email = None

    email_verified_raw = claims.get("email_verified", False)
    email_verified = bool(email_verified_raw)

    name = claims.get("name")
    if name is not None and not isinstance(name, str):
        name = None

    picture = claims.get("picture")
    if picture is not None and not isinstance(picture, str):
        picture = None

    return GoogleIdInfo(
        sub=sub,
        email=email,
        email_verified=email_verified,
        name=name,
        picture=picture,
    )
