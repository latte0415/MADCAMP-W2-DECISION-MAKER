from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Event, Assumption
from app.schemas.dev.assumption import AssumptionCreate, AssumptionUpdate, AssumptionResponse

router = APIRouter()


@router.get("/events/{event_id}/assumptions", response_model=List[AssumptionResponse])
async def get_assumptions_by_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트별 전제 목록 조회"""
    assumptions = db.query(Assumption).filter(Assumption.event_id == event_id).all()
    return assumptions


@router.get("/assumptions/{assumption_id}", response_model=AssumptionResponse)
async def get_assumption(
    assumption_id: UUID,
    db: Session = Depends(get_db)
):
    """전제 단일 조회"""
    assumption = db.query(Assumption).filter(Assumption.id == assumption_id).first()
    if not assumption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption with id {assumption_id} not found"
        )
    return assumption


@router.post("/events/{event_id}/assumptions", response_model=AssumptionResponse, status_code=status.HTTP_201_CREATED)
async def create_assumption(
    event_id: UUID,
    assumption: AssumptionCreate,
    db: Session = Depends(get_db)
):
    """전제 생성"""
    # event_id 검증
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )
    
    assumption_data = assumption.model_dump()
    assumption_data['event_id'] = event_id
    db_assumption = Assumption(**assumption_data)
    db.add(db_assumption)
    db.commit()
    db.refresh(db_assumption)
    return db_assumption


@router.patch("/assumptions/{assumption_id}", response_model=AssumptionResponse)
async def update_assumption(
    assumption_id: UUID,
    assumption_update: AssumptionUpdate,
    db: Session = Depends(get_db)
):
    """전제 수정"""
    db_assumption = db.query(Assumption).filter(Assumption.id == assumption_id).first()
    if not db_assumption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption with id {assumption_id} not found"
        )
    
    update_data = assumption_update.model_dump(exclude_unset=True)
    if update_data:
        if 'updated_at' not in update_data:
            from datetime import datetime, timezone
            update_data['updated_at'] = datetime.now(timezone.utc)
    
    for field, value in update_data.items():
        setattr(db_assumption, field, value)
    
    db.commit()
    db.refresh(db_assumption)
    return db_assumption


@router.delete("/assumptions/{assumption_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assumption(
    assumption_id: UUID,
    db: Session = Depends(get_db)
):
    """전제 삭제"""
    db_assumption = db.query(Assumption).filter(Assumption.id == assumption_id).first()
    if not db_assumption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption with id {assumption_id} not found"
        )
    db.delete(db_assumption)
    db.commit()
    return None
