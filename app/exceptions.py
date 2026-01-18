from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from os import getenv


class AppException(Exception):
    """애플리케이션 커스텀 예외 베이스 클래스"""
    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail or message
        super().__init__(self.message)

    @property
    def status_code(self) -> int:
        """HTTP 상태 코드 반환"""
        return status.HTTP_500_INTERNAL_SERVER_ERROR


class NotFoundError(AppException):
    """리소스를 찾을 수 없음 (404)"""
    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND


class ValidationError(AppException):
    """입력 검증 실패 (400)"""
    @property
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST


class ConflictError(AppException):
    """리소스 충돌 (409)"""
    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT


class ForbiddenError(AppException):
    """권한 없음 (403)"""
    @property
    def status_code(self) -> int:
        return status.HTTP_403_FORBIDDEN


class InternalError(AppException):
    """예상치 못한 서버 에러 (500)"""
    pass


def is_development() -> bool:
    """개발 환경인지 확인"""
    env = getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """커스텀 애플리케이션 예외 핸들러"""
    response_data = {
        "error": exc.__class__.__name__,
        "message": exc.message,
        "detail": exc.detail,
    }
    
    # 개발 환경에서만 스택 트레이스 포함
    if is_development():
        import traceback
        response_data["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """SQLAlchemy IntegrityError 핸들러 (중복 키, 외래 키 제약 등)"""
    error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    # 중복 키 에러 감지
    if "unique" in error_message.lower() or "duplicate" in error_message.lower():
        app_exc = ConflictError(
            message="Resource conflict",
            detail=f"Resource already exists: {error_message}"
        )
    else:
        app_exc = ConflictError(
            message="Database integrity error",
            detail=error_message
        )
    
    return await app_exception_handler(request, app_exc)


async def sqlalchemy_operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """SQLAlchemy OperationalError 핸들러 (DB 연결 에러 등)"""
    error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    app_exc = InternalError(
        message="Database operation failed",
        detail=error_message if is_development() else "Database operation failed"
    )
    
    return await app_exception_handler(request, app_exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러 (예상치 못한 에러)"""
    app_exc = InternalError(
        message="Internal server error",
        detail=str(exc) if is_development() else "An unexpected error occurred"
    )
    
    # 개발 환경에서만 원본 예외 정보 포함
    if is_development():
        import traceback
        app_exc.detail = f"{app_exc.detail}\n\nTraceback:\n{traceback.format_exc()}"
    
    return await app_exception_handler(request, app_exc)
