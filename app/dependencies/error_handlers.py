from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError, OperationalError

from app.exceptions import (
    AppException,
    app_exception_handler,
    sqlalchemy_integrity_error_handler,
    sqlalchemy_operational_error_handler,
    general_exception_handler,
)


def register_error_handlers(app: FastAPI) -> None:
    """FastAPI 앱에 전역 예외 핸들러를 등록"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
    app.add_exception_handler(OperationalError, sqlalchemy_operational_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
