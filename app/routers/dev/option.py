from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db import get_db
from app.models import Event, Option
from app.exceptions import NotFoundError, ConflictError, InternalError
from app.schemas.dev.option import OptionCreate, OptionUpdate, OptionResponse

router = APIRouter()


@router.get("/events/{event_id}/options", response_model=List[OptionResponse])
async def get_options_by_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트별 선택지 목록 조회"""
    options = db.query(Option).filter(Option.event_id == event_id).all()
    return options


@router.get("/options/{option_id}", response_model=OptionResponse)
async def get_option(
    option_id: UUID,
    db: Session = Depends(get_db)
):
    """선택지 단일 조회"""
    option = db.query(Option).filter(Option.id == option_id).first()
    if not option:
        raise NotFoundError(
            message="Option not found",
            detail=f"Option with id {option_id} not found"
        )
    return option


@router.post("/events/{event_id}/options", response_model=OptionResponse, status_code=status.HTTP_201_CREATED)
async def create_option(
    event_id: UUID,
    option: OptionCreate,
    db: Session = Depends(get_db)
):
    """선택지 생성"""
    # event_id 검증
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    
    try:
        option_data = option.model_dump()
        option_data['event_id'] = event_id
        db_option = Option(**option_data)
        db.add(db_option)
        db.commit()
        db.refresh(db_option)
        return db_option
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Option creation failed",
            detail=f"Failed to create option: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to create option due to database error: {str(e)}"
        ) from e


@router.patch("/options/{option_id}", response_model=OptionResponse)
async def update_option(
    option_id: UUID,
    option_update: OptionUpdate,
    db: Session = Depends(get_db)
):
    """선택지 수정"""
    db_option = db.query(Option).filter(Option.id == option_id).first()
    if not db_option:
        raise NotFoundError(
            message="Option not found",
            detail=f"Option with id {option_id} not found"
        )
    
    try:
        update_data = option_update.model_dump(exclude_unset=True)
        if update_data:
            from datetime import datetime, timezone
            update_data['updated_at'] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(db_option, field, value)
        
        db.commit()
        db.refresh(db_option)
        return db_option
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Option update failed",
            detail=f"Failed to update option: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to update option due to database error: {str(e)}"
        ) from e


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(
    option_id: UUID,
    db: Session = Depends(get_db)
):
    """선택지 삭제"""
    db_option = db.query(Option).filter(Option.id == option_id).first()
    if not db_option:
        raise NotFoundError(
            message="Option not found",
            detail=f"Option with id {option_id} not found"
        )
    
    try:
        db.delete(db_option)
        db.commit()
        return None
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to delete option due to database error: {str(e)}"
        ) from e
