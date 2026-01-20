from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.event import MembershipStatusType


class MembershipResponse(BaseModel):
    """멤버십 승인/거부 응답"""
    message: str
    membership_id: UUID
    membership_status: MembershipStatusType

    class Config:
        from_attributes = True


class BulkMembershipResponse(BaseModel):
    """멤버십 일괄 처리 응답"""
    message: str
    approved_count: int | None = None
    rejected_count: int | None = None
    failed_count: int | None = None


class MembershipListItemResponse(BaseModel):
    """멤버십 리스트 항목"""
    user_id: UUID
    membership_id: UUID
    name: str | None  # 사용자 이름
    email: str | None  # 사용자 이메일
    status: MembershipStatusType
    created_at: datetime
    joined_at: datetime | None
    is_me: bool  # 본인 여부
    is_admin: bool  # 관리자 여부

    class Config:
        from_attributes = True
