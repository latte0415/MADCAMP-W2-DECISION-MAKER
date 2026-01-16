from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from os import getenv
from typing import Generator

class Base(DeclarativeBase):
    pass

# TODO: 환경 변수 설정 필요
DATABASE_URL = getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # 임시: DATABASE_URL이 없을 때 (개발 중)
    SessionLocal = None


def get_db() -> Generator:
    """FastAPI 의존성으로 사용할 DB 세션"""
    # TODO: 실제 DB 연결 설정 필요
    if SessionLocal is None:
        # 임시: 실제 DB 연결 없이 개발 중
        yield None  # 실제 구현 시 SessionLocal() 사용
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
