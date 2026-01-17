from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CriterionBase(BaseModel):
    content: str


class CriterionCreate(CriterionBase):
    created_by: UUID


class CriterionUpdate(BaseModel):
    content: str | None = None
    conclusion: str | None = None
    updated_by: UUID | None = None


class CriterionResponse(CriterionBase):
    id: UUID
    event_id: UUID
    conclusion: str | None = None
    created_at: datetime
    created_by: UUID
    updated_at: datetime | None = None
    updated_by: UUID | None = None

    class Config:
        from_attributes = True
