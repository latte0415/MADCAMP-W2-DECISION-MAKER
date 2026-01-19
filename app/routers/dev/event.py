from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db import get_db
from app.models import Event
from app.exceptions import NotFoundError, ConflictError, InternalError
from app.schemas.dev.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """이벤트 목록 조회"""
    events = db.query(Event).offset(skip).limit(limit).all()
    return events


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트 단일 조회"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    return event


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    """이벤트 생성"""
    try:
        db_event = Event(**event.model_dump())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Event creation failed",
            detail=f"Failed to create event: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to create event due to database error: {str(e)}"
        ) from e


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    db: Session = Depends(get_db)
):
    """이벤트 수정"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    
    try:
        update_data = event_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        db.commit()
        db.refresh(db_event)
        return db_event
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Event update failed",
            detail=f"Failed to update event: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to update event due to database error: {str(e)}"
        ) from e


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트 삭제"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    
    try:
        db.delete(db_event)
        db.commit()
        return None
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to delete event due to database error: {str(e)}"
        ) from e
