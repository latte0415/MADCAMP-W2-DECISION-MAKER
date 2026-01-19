# app/schemas/auth.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -----------------------------
# User-facing models
# -----------------------------

class CurrentUser(BaseModel):
    """Minimal, response-safe user info (also usable as auth context)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None
    name: str | None = None
    is_active: bool = True


class UserResponse(BaseModel):
    """Response model for GET /me."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None
    name: str | None = None
    is_active: bool
    created_at: datetime | None = None


# -----------------------------
# Requests (JSON body)
# -----------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class GoogleLoginRequest(BaseModel):
    """
    Frontend sends the Google ID token (JWT) it received from Google Identity Services.
    Backend verifies it and issues *our* access token + refresh cookie.
    """
    id_token: str = Field(min_length=1)

class PasswordResetRequest(BaseModel):
    """
    POST /auth/password-reset/request
    """
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """
    POST /auth/password-reset/confirm
    """
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=20)


class UpdateNameRequest(BaseModel):
    """
    PATCH /auth/me/name
    """
    name: str = Field(min_length=1, max_length=100)

# -----------------------------
# Responses
# -----------------------------

class TokenResponse(BaseModel):
    """
    Response for POST /signup, POST /login, POST /refresh.

    Refresh token is stored in an HttpOnly cookie, so it is NOT included here.
    """
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser


class MessageResponse(BaseModel):
    """Response for POST /logout, as well as for POST /auth/password-reset/confirm and POST /auth/password-reset/request"""
    message: str
