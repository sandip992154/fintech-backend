from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from database.database import get_db
from services.models.transaction_models import CommissionStructure
from services.schemas.transaction_schemas import (
    CommissionStructureCreate,
    CommissionStructureUpdate,
    CommissionStructureOut
)

router = APIRouter(prefix="/commission", tags=["Commission Management"])

@router.post("/structure/create", response_model=CommissionStructureOut)
async def create_commission_structure(
    commission: CommissionStructureCreate,
    db: Session = Depends(get_db)
):
    # Check if structure already exists
    existing = db.query(CommissionStructure).filter(
        CommissionStructure.role_id == commission.role_id,
        CommissionStructure.service_id == commission.service_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commission structure already exists for this role and service"
        )
    
    db_commission = CommissionStructure(**commission.model_dump())
    db.add(db_commission)
    db.commit()
    db.refresh(db_commission)
    
    return db_commission

@router.put("/structure/{commission_id}", response_model=CommissionStructureOut)
async def update_commission_structure(
    commission_id: int,
    commission: CommissionStructureUpdate,
    db: Session = Depends(get_db)
):
    db_commission = db.query(CommissionStructure).filter(
        CommissionStructure.id == commission_id
    ).first()
    
    if not db_commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission structure not found"
        )
    
    for key, value in commission.model_dump(exclude_unset=True).items():
        setattr(db_commission, key, value)
    
    db.commit()
    db.refresh(db_commission)
    
    return db_commission

@router.get("/structure/role/{role_id}", response_model=List[CommissionStructureOut])
async def get_commission_by_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    commissions = db.query(CommissionStructure).filter(
        CommissionStructure.role_id == role_id,
        CommissionStructure.is_active == True
    ).all()
    
    return commissions

@router.get("/structure/service/{service_id}", response_model=List[CommissionStructureOut])
async def get_commission_by_service(
    service_id: int,
    db: Session = Depends(get_db)
):
    commissions = db.query(CommissionStructure).filter(
        CommissionStructure.service_id == service_id,
        CommissionStructure.is_active == True
    ).all()
    
    return commissions

@router.get("/calculate/{role_id}/{service_id}/{amount}")
async def calculate_commission(
    role_id: int,
    service_id: int,
    amount: Decimal,
    db: Session = Depends(get_db)
):
    commission = db.query(CommissionStructure).filter(
        CommissionStructure.role_id == role_id,
        CommissionStructure.service_id == service_id,
        CommissionStructure.is_active == True
    ).first()
    
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission structure not found"
        )
    
    if amount < commission.min_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount should be greater than {commission.min_amount}"
        )
    
    if commission.max_amount and amount > commission.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount should be less than {commission.max_amount}"
        )
    
    commission_amount = (amount * commission.commission_percentage) / 100
    charge_amount = (amount * commission.charge_percentage) / 100
    
    return {
        "base_amount": amount,
        "commission_amount": commission_amount,
        "charge_amount": charge_amount,
        "total_earning": commission_amount - charge_amount,
        "commission_percentage": commission.commission_percentage,
        "charge_percentage": commission.charge_percentage
    }

@router.delete("/structure/{commission_id}")
async def delete_commission_structure(
    commission_id: int,
    db: Session = Depends(get_db)
):
    commission = db.query(CommissionStructure).filter(
        CommissionStructure.id == commission_id
    ).first()
    
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission structure not found"
        )
    
    commission.is_active = False
    db.commit()
    
    return {"message": "Commission structure deactivated successfully"}
