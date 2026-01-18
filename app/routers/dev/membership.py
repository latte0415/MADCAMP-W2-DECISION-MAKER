from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db import get_db
from app.models import Event, EventMembership
from app.exceptions import NotFoundError, ConflictError, InternalError
from app.schemas.dev.membership import (
    EventMembershipCreate, EventMembershipUpdate, EventMembershipResponse
)

router = APIRouter()


@router.get("/events/{event_id}/memberships", response_model=List[EventMembershipResponse])
async def get_memberships_by_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """이벤트별 멤버십 목록 조회"""
    memberships = db.query(EventMembership).filter(EventMembership.event_id == event_id).all()
    return memberships


@router.get("/memberships/{membership_id}", response_model=EventMembershipResponse)
async def get_membership(
    membership_id: UUID,
    db: Session = Depends(get_db)
):
    """멤버십 단일 조회"""
    membership = db.query(EventMembership).filter(EventMembership.id == membership_id).first()
    if not membership:
        raise NotFoundError(
            message="Membership not found",
            detail=f"EventMembership with id {membership_id} not found"
        )
    return membership


@router.post("/events/{event_id}/memberships", response_model=EventMembershipResponse, status_code=status.HTTP_201_CREATED)
async def create_membership(
    event_id: UUID,
    membership: EventMembershipCreate,
    db: Session = Depends(get_db)
):
    """멤버십 생성"""
    # event_id 검증
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundError(
            message="Event not found",
            detail=f"Event with id {event_id} not found"
        )
    
    try:
        membership_data = membership.model_dump()
        membership_data['event_id'] = event_id
        db_membership = EventMembership(**membership_data)
        db.add(db_membership)
        db.commit()
        db.refresh(db_membership)
        return db_membership
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Membership creation failed",
            detail=f"Failed to create membership: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to create membership due to database error: {str(e)}"
        ) from e


@router.patch("/memberships/{membership_id}", response_model=EventMembershipResponse)
async def update_membership(
    membership_id: UUID,
    membership_update: EventMembershipUpdate,
    db: Session = Depends(get_db)
):
    """멤버십 수정"""
    db_membership = db.query(EventMembership).filter(EventMembership.id == membership_id).first()
    if not db_membership:
        raise NotFoundError(
            message="Membership not found",
            detail=f"EventMembership with id {membership_id} not found"
        )
    
    try:
        update_data = membership_update.model_dump(exclude_unset=True)
        if update_data:
            from datetime import datetime, timezone
            update_data['updated_at'] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(db_membership, field, value)
        
        db.commit()
        db.refresh(db_membership)
        return db_membership
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            message="Membership update failed",
            detail=f"Failed to update membership: {str(e)}"
        ) from e
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to update membership due to database error: {str(e)}"
        ) from e


@router.delete("/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_membership(
    membership_id: UUID,
    db: Session = Depends(get_db)
):
    """멤버십 삭제"""
    db_membership = db.query(EventMembership).filter(EventMembership.id == membership_id).first()
    if not db_membership:
        raise NotFoundError(
            message="Membership not found",
            detail=f"EventMembership with id {membership_id} not found"
        )
    
    try:
        db.delete(db_membership)
        db.commit()
        return None
    except OperationalError as e:
        db.rollback()
        raise InternalError(
            message="Database operation failed",
            detail=f"Failed to delete membership due to database error: {str(e)}"
        ) from e
