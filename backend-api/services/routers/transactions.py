from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
from datetime import datetime

from database.database import get_db
from services.auth.auth import get_current_user

router = APIRouter(tags=["Transactions"])

# Demo Wallet Routes
@router.post("/wallet/create")
async def create_wallet(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Create Wallet"""
    return {
        "id": f"WALLET{uuid.uuid4().hex[:8].upper()}",
        "balance": 0.0,
        "currency": "INR",
        "status": "active",
        "created_at": datetime.now().isoformat()
    }

@router.post("/wallet/topup")
async def wallet_topup(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Wallet Topup"""
    amount = request_data.get("amount", 1000)
    return {
        "transaction_id": f"TOP{uuid.uuid4().hex[:10].upper()}",
        "new_balance": 5000.0 + amount,
        "amount": amount,
        "payment_method": request_data.get("payment_method", "upi"),
        "status": "success",
        "reference_id": request_data.get("reference_id")
    }

@router.post("/transfer")
async def wallet_transfer(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Wallet Transfer"""
    return {
        "transaction_id": f"TXN{uuid.uuid4().hex[:10].upper()}",
        "amount": request_data.get("amount", 100),
        "to_user_id": request_data.get("to_user_id"),
        "description": request_data.get("description", "Transfer"),
        "status": "success",
        "fee": 0,
        "net_amount": request_data.get("amount", 100)
    }

@router.get("/list")
async def get_transactions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Get Transactions List"""
    return [
        {
            "id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "amount": 1000.0,
            "type": "credit",
            "description": "Wallet topup",
            "status": "success",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "amount": 500.0,
            "type": "debit",
            "description": "Transfer to user",
            "status": "success", 
            "created_at": datetime.now().isoformat()
        }
    ]

@router.get("/wallet/balance")
async def get_wallet_balance(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Get Wallet Balance"""
    return {
        "balance": 4500.0,
        "currency": "INR",
        "last_updated": datetime.now().isoformat(),
        "wallet_id": f"WALLET{uuid.uuid4().hex[:8].upper()}"
    }

@router.get("/history")
async def get_transaction_history(
    start_date: str = None,
    end_date: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demo Get Transaction History"""
    return [
        {
            "id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "amount": 2000.0,
            "type": "credit",
            "description": "AEPS cash withdrawal",
            "status": "success",
            "created_at": "2025-08-15T10:30:00",
            "reference_id": f"AEPS{uuid.uuid4().hex[:6].upper()}"
        },
        {
            "id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "amount": 500.0,
            "type": "debit",
            "description": "FASTag recharge",
            "status": "success",
            "created_at": "2025-08-16T14:20:00",
            "reference_id": f"FAS{uuid.uuid4().hex[:6].upper()}"
        },
        {
            "id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "amount": 1000.0,
            "type": "credit",
            "description": "Wallet topup via UPI",
            "status": "success",
            "created_at": "2025-08-17T09:15:00",
            "reference_id": f"UPI{uuid.uuid4().hex[:6].upper()}"
        }
    ]
