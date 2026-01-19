from pydantic import BaseModel
from uuid import UUID


class OptionInfo(BaseModel):
    """선택지 정보 (공통)"""
    id: UUID
    content: str

    class Config:
        from_attributes = True


class AdminInfo(BaseModel):
    """관리자 정보 (공통)"""
    id: UUID
    email: str

    class Config:
        from_attributes = True
