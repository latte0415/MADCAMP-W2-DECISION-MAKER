from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class OptionBase(BaseModel):
    content: str


class OptionCreate(OptionBase):
    created_by: UUID


class OptionUpdate(BaseModel):
    content: str | None = None


class OptionResponse(OptionBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
