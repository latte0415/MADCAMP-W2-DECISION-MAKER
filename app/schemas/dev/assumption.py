from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AssumptionBase(BaseModel):
    content: str


class AssumptionCreate(AssumptionBase):
    created_by: UUID


class AssumptionUpdate(BaseModel):
    content: str | None = None
    updated_by: UUID | None = None


class AssumptionResponse(AssumptionBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime | None = None
    updated_by: UUID | None = None

    class Config:
        from_attributes = True
