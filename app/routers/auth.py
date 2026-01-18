from __future__ import annotations

import os
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.dependencies import get_auth_service, get_current_user
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    SignupRequest,
    TokenResponse,
    UserResponse,
    GoogleLoginRequest
)
from app.services.auth import (
    AuthService,
    EmailAlreadyExists,
    InactiveUser,
    InvalidCredentials,
    InvalidGoogleToken,
    LocalLoginNotAvailable,
    InvalidRefreshToken,
)

router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"


def _cookie_secure() -> bool:
    """
    For local HTTP dev, Secure cookies won't be set by the browser.
    Use COOKIE_SECURE=true in production (HTTPS).
    """
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _refresh_cookie_max_age_seconds() -> int:
    days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    return int(timedelta(days=days).total_seconds())


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        # Only send this cookie to the refresh endpoint. + THE LOGOUT ENDPOINT AS WELL
        # This reduces accidental exposure to other endpoints.
        path="/api/auth",
        max_age=_refresh_cookie_max_age_seconds(),
    )


def _clear_refresh_cookie(response: Response) -> None:
    # Path must match the one used to set it
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    req: SignupRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        result = service.signup(email=req.email, password=req.password)
    except EmailAlreadyExists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 이메일입니다.")

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        user=result.user,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        result = service.login(email=req.email, password=req.password)
    except LocalLoginNotAvailable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="구글 계정과 연결된 이메일입니다. 구글로 로그인해주세요.",
        )
    except InvalidCredentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일/비밀번호가 일치하지 않습니다.")
    except InactiveUser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비활성화된 사용자입니다.")

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        user=result.user,
    )

@router.post("/google", response_model=TokenResponse)
def login_with_google(
    req: GoogleLoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Google login:
    - frontend sends Google ID token
    - backend verifies it and issues our access token + sets refresh cookie
    """
    try:
        result = service.login_google(id_token=req.id_token)
    except InvalidGoogleToken:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="구글 토큰 오류가 발생하였습니다.")
    except InactiveUser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비활성화된 사용자입니다.")

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        user=result.user,
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    if not refresh_token:
        # Missing cookie => not authenticated
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        result = service.refresh(refresh_token=refresh_token)
    except InvalidRefreshToken:
        # Clear cookie to prevent client retry loops
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Rotation: replace cookie with new refresh token
    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        user=result.user,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    # Best-effort logout: do not leak token existence/validity
    if refresh_token:
        try:
            service.logout(refresh_token=refresh_token)
        except Exception:
            pass

    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    # get_current_user returns the User ORM instance (recommended).
    return UserResponse.model_validate(current_user)
