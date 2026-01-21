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


def is_korean() -> bool:
    """한국어 환경인지 확인"""
    language = getenv("LANGUAGE", "").upper()
    return language == "KR"


def translate_message(message: str) -> str:
    """에러 메시지를 한국어로 번역"""
    if not is_korean():
        return message
    
    # 자주 사용되는 에러 메시지 번역
    translations = {
        "Resource conflict": "리소스 충돌",
        "Resource already exists": "리소스가 이미 존재합니다",
        "Database integrity error": "데이터베이스 무결성 오류",
        "Database operation failed": "데이터베이스 작업 실패",
        "Internal server error": "내부 서버 오류",
        "An unexpected error occurred": "예상치 못한 오류가 발생했습니다",
        "Event not found": "이벤트를 찾을 수 없습니다",
        "User not found": "사용자를 찾을 수 없습니다",
        "Proposal not found": "제안을 찾을 수 없습니다",
        "Membership not found": "멤버십을 찾을 수 없습니다",
        "Vote not found": "투표를 찾을 수 없습니다",
        "Comment not found": "댓글을 찾을 수 없습니다",
        "Option not found": "선택지를 찾을 수 없습니다",
        "Assumption not found": "전제를 찾을 수 없습니다",
        "Criterion not found": "기준을 찾을 수 없습니다",
        "Forbidden": "권한이 없습니다",
        "Unauthorized": "인증이 필요합니다",
        "Validation failed": "검증 실패",
        "Invalid input": "잘못된 입력",
        "Event creation failed": "이벤트 생성 실패",
        "Event update failed": "이벤트 수정 실패",
        "Event deletion failed": "이벤트 삭제 실패",
        "Proposal not pending": "제안이 대기 중 상태가 아닙니다",
        "Only accepted members can": "승인된 멤버만",
        "Only admin can": "관리자만",
        "can only be performed for PENDING proposals": "대기 중인 제안에만 수행할 수 있습니다",
        "can only be performed for IN_PROGRESS events": "진행 중인 이벤트에만 수행할 수 있습니다",
        "not found for this event": "이 이벤트에서 찾을 수 없습니다",
        "Duplicate proposal": "중복된 제안",
        "Assumption is deleted": "전제가 삭제되었습니다",
        "Invalid proposal_content": "잘못된 제안 내용",
        "Missing proposal_content": "제안 내용이 없습니다",
        "Invalid assumption_id": "잘못된 전제 ID",
        "Missing assumption_id": "전제 ID가 없습니다",
        "Invalid criteria_id": "잘못된 기준 ID",
        "Missing criteria_id": "기준 ID가 없습니다",
        "Already voted": "이미 투표했습니다",
        "Membership not accepted": "멤버십이 승인되지 않았습니다",
        "Event not in progress": "이벤트가 진행 중이 아닙니다",
        "Max membership exceeded": "최대 인원을 초과했습니다",
        "Cannot delete own membership": "자신의 멤버십을 삭제할 수 없습니다",
        "Cannot reject own membership": "자신의 멤버십을 거부할 수 없습니다",
        "Membership approved successfully": "멤버십이 성공적으로 승인되었습니다",
        "Membership rejected successfully": "멤버십이 성공적으로 거부되었습니다",
        "Bulk approval completed": "일괄 승인이 완료되었습니다",
        "Bulk rejection completed": "일괄 거부가 완료되었습니다",
        "Logged out successfully": "로그아웃되었습니다",
        "Vote created successfully": "투표가 성공적으로 생성되었습니다",
        "Vote deleted successfully": "투표가 성공적으로 삭제되었습니다",
        "with id": "ID가",
        "not found": "를 찾을 수 없습니다",
    }
    
    # 정확한 매칭 우선
    if message in translations:
        return translations[message]
    
    # 부분 매칭으로 번역 (긴 패턴부터 매칭)
    sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
    for en_msg, kr_msg in sorted_translations:
        if en_msg in message:
            return message.replace(en_msg, kr_msg)
    
    return message


def translate_detail(detail: str) -> str:
    """에러 상세 메시지를 한국어로 번역"""
    if not is_korean():
        return detail
    
    # 메시지 번역
    translated = translate_message(detail)
    
    # 자주 사용되는 패턴 번역
    patterns = {
        "Event with id": "ID가",
        "User with id": "ID가",
        "Proposal with id": "ID가",
        "Membership with id": "ID가",
        "Vote with id": "ID가",
        "Comment with id": "ID가",
        "Option with id": "ID가",
        "Assumption with id": "ID가",
        "Criterion with id": "ID가",
        "not found for this event": "이 이벤트에서 찾을 수 없습니다",
        "not found": "를 찾을 수 없습니다",
        "already exists": "이미 존재합니다",
        "Resource already exists:": "리소스가 이미 존재합니다:",
        "Failed to": "실패했습니다:",
        "due to database error:": "데이터베이스 오류로 인해:",
        "You already have a pending proposal": "이미 대기 중인 제안이 있습니다",
        "can only be performed for": "다음에만 수행할 수 있습니다:",
        "PENDING proposals": "대기 중인 제안",
        "IN_PROGRESS events": "진행 중인 이벤트",
    }
    
    # 긴 패턴부터 매칭
    sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[0]), reverse=True)
    for en_pattern, kr_pattern in sorted_patterns:
        if en_pattern in translated:
            translated = translated.replace(en_pattern, kr_pattern)
    
    return translated


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """커스텀 애플리케이션 예외 핸들러"""
    # 언어에 따라 메시지 번역
    translated_message = translate_message(exc.message)
    translated_detail = translate_detail(exc.detail)
    
    response_data = {
        "error": exc.__class__.__name__,
        "message": translated_message,
        "detail": translated_detail,
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
        if is_korean():
            app_exc = ConflictError(
                message="리소스 충돌",
                detail=f"리소스가 이미 존재합니다: {error_message}"
            )
        else:
            app_exc = ConflictError(
                message="Resource conflict",
                detail=f"Resource already exists: {error_message}"
            )
    else:
        if is_korean():
            app_exc = ConflictError(
                message="데이터베이스 무결성 오류",
                detail=error_message
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
    
    if is_korean():
        app_exc = InternalError(
            message="데이터베이스 작업 실패",
            detail=error_message if is_development() else "데이터베이스 작업 실패"
        )
    else:
        app_exc = InternalError(
            message="Database operation failed",
            detail=error_message if is_development() else "Database operation failed"
        )
    
    return await app_exception_handler(request, app_exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러 (예상치 못한 에러)"""
    if is_korean():
        app_exc = InternalError(
            message="내부 서버 오류",
            detail=str(exc) if is_development() else "예상치 못한 오류가 발생했습니다"
        )
    else:
        app_exc = InternalError(
            message="Internal server error",
            detail=str(exc) if is_development() else "An unexpected error occurred"
        )
    
    # 개발 환경에서만 원본 예외 정보 포함
    if is_development():
        import traceback
        app_exc.detail = f"{app_exc.detail}\n\nTraceback:\n{traceback.format_exc()}"
    
    return await app_exception_handler(request, app_exc)
