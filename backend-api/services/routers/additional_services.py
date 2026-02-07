from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid

from database.database import get_db
from services.auth.auth import get_current_user

router = APIRouter()

# AEPS Routes - Demo Implementation
@router.post("/aeps/balance-enquiry")
async def aeps_balance_enquiry(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo AEPS Balance Enquiry"""
    return {
        "balance": 5000.50,
        "status": "success",
        "message": "Balance enquiry successful",
        "bank_name": "Demo Bank",
        "account_number": "XXXX1234"
    }

@router.post("/aeps/cash-withdrawal")
async def aeps_cash_withdrawal(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo AEPS Cash Withdrawal"""
    return {
        "transaction_id": f"AEPS{uuid.uuid4().hex[:10].upper()}",
        "status": "success", 
        "amount": request_data.get("amount", 1000),
        "remaining_balance": 4000.50,
        "message": "Cash withdrawal successful"
    }

# MATM Routes - Demo Implementation  
@router.post("/matm/initialize")
async def matm_initialize(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo MATM Initialize"""
    return {
        "status": "initialized",
        "device_id": request_data.get("device_id"),
        "session_id": f"MATM{uuid.uuid4().hex[:8].upper()}",
        "message": "MATM device initialized successfully"
    }

@router.post("/matm/transaction")
async def matm_transaction(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo MATM Transaction"""
    return {
        "transaction_id": f"MATM{uuid.uuid4().hex[:10].upper()}",
        "status": "success",
        "amount": request_data.get("amount", 1000),
        "transaction_type": request_data.get("transaction_type", "withdrawal"),
        "message": "MATM transaction successful"
    }

# Insurance Routes - Demo Implementation
@router.post("/insurance/get-quotes")
async def insurance_get_quotes(
    request_data: Dict[str, Any], 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Insurance Quotes"""
    return {
        "quotes": [
            {
                "provider": "Demo Insurance Co.",
                "plan_name": "Life Cover Premium",
                "premium": 15000,
                "coverage": request_data.get("customer_data", {}).get("coverage_amount", 1000000),
                "quote_id": f"INS{uuid.uuid4().hex[:8].upper()}"
            },
            {
                "provider": "Demo Life Insurance",
                "plan_name": "Term Life Pro",
                "premium": 12000,
                "coverage": request_data.get("customer_data", {}).get("coverage_amount", 1000000),
                "quote_id": f"INS{uuid.uuid4().hex[:8].upper()}"
            }
        ],
        "status": "success"
    }

# PAN Card Routes - Demo Implementation
@router.post("/pan/apply")
async def pan_card_application(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo PAN Card Application"""
    return {
        "application_number": f"PAN{uuid.uuid4().hex[:10].upper()}",
        "status": "submitted",
        "estimated_days": 15,
        "application_fee": 107,
        "message": "PAN card application submitted successfully"
    }

# FASTag Routes - Demo Implementation
@router.post("/fastag/recharge")
async def fastag_recharge(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo FASTag Recharge"""
    return {
        "transaction_id": f"FAS{uuid.uuid4().hex[:10].upper()}",
        "status": "success",
        "amount": request_data.get("amount", 500),
        "vehicle_number": request_data.get("vehicle_number"),
        "new_balance": 1500,
        "message": "FASTag recharge successful"
    }
