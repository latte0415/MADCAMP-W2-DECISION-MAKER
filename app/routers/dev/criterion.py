from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db import get_db
from app.models import Event, Criterion
from app.exceptions import NotFoundError, ConflictError, InternalError
from app.schemas.dev.criterion import CriterionCreate, CriterionUpdate, CriterionResponse

router = APIRouter()


@router.get("/events/{event_id}/criteria", response_model=List[CriterionResponse])
async def get_criteria_by_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트별 기준 목록 조회"""
    criteria = db.query(Criterion).filter(Criterion.event_id == event_id).all()
    return criteria


@router.get("/criteria/{criterion_id}", response_model=CriterionResponse)
async def get_criterion(
    criterion_id: UUID,
    db: Session = Depends(get_db)
):
    """기준 단일 조회"""
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not criterion:
        raise NotFoundError(
            message="Criterion not found",
            detail=f"Criterion with id {criterion_id} not found"
        )
    return criterion


@router.post("/events/{event_id}/criteria", response_model=CriterionResponse, status_code=status.HTTP_201_CREATED)
async def create_criterion(
    event_id: UUID,
    criterion: CriterionCreate,
    db: Session = Depends(get_db)
):
    """기준 생성"""
    # event_id 검증
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    
    try:
        criterion_data = criterion.model_dump()
        criterion_data['event_id'] = event_id
        db_criterion = Criterion(**criterion_data)
        db.add(db_criterion)
        db.commit()
        db.refresh(db_criterion)
        return db_criterion
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Criterion creation failed",
            detail=f"Failed to create criterion: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to create criterion due to database error: {str(e)}"
        ) from e


@router.patch("/criteria/{criterion_id}", response_model=CriterionResponse)
async def update_criterion(
    criterion_id: UUID,
    criterion_update: CriterionUpdate,
    db: Session = Depends(get_db)
):
    """기준 수정"""
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise NotFoundError(
            message="Criterion not found",
            detail=f"Criterion with id {criterion_id} not found"
        )
    
    try:
        update_data = criterion_update.model_dump(exclude_unset=True)
        if update_data:
            if 'updated_at' not in update_data:
                from datetime import datetime, timezone
                update_data['updated_at'] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(db_criterion, field, value)
        
        db.commit()
        db.refresh(db_criterion)
        return db_criterion
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Criterion update failed",
            detail=f"Failed to update criterion: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to update criterion due to database error: {str(e)}"
        ) from e


@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_criterion(
    criterion_id: UUID,
    db: Session = Depends(get_db)
):
    """기준 삭제"""
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise NotFoundError(
            message="Criterion not found",
            detail=f"Criterion with id {criterion_id} not found"
        )
    
    try:
        db.delete(db_criterion)
        db.commit()
        return None
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to delete criterion due to database error: {str(e)}"
        ) from e
