from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


# ============================================================================
# Request Schemas
# ============================================================================

class CommentCreateRequest(BaseModel):
    """코멘트 생성 요청"""
    content: str


class CommentUpdateRequest(BaseModel):
    """코멘트 수정 요청"""
    content: str


# ============================================================================
# Response Schemas
# ============================================================================

class CommentCreatorInfo(BaseModel):
    """코멘트 작성자 정보"""
    id: UUID
    name: str | None
    email: str | None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """코멘트 응답"""
    id: UUID
    criterion_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime | None
    created_by: UUID
    creator: CommentCreatorInfo | None = None

    class Config:
        from_attributes = True


class CommentCountResponse(BaseModel):
    """코멘트 수 응답"""
    count: int
