from pydantic import BaseModel
from uuid import UUID


class CurrentUser(BaseModel):
    """현재 인증된 사용자 정보 (Context 객체)"""
    id: UUID
    email: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 변환 가능
