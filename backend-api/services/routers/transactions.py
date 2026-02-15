from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.transaction_models import Wallet, WalletTransaction
from services.models.models import User
from services.schemas.transaction_schemas import WalletOut, WalletTransactionOut, WalletTopupRequest

router = APIRouter(tags=["Transactions"])

# ======================== WALLET ENDPOINTS ========================

@router.post("/wallet/create")
async def create_wallet(
    request_data: Dict[str, Any] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new wallet for the current user"""
    try:
        user_id = current_user.id
        
        # Check if wallet already exists
        existing_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet already exists for this user"
            )
        
        # Create new wallet
        new_wallet = Wallet(
            user_id=user_id,
            balance=0.0,
            is_active=True,
            last_updated=datetime.utcnow()
        )
        
        db.add(new_wallet)
        db.commit()
        db.refresh(new_wallet)
        
        return {
            "success": True,
            "message": "Wallet created successfully",
            "data": {
                "id": new_wallet.id,
                "user_id": new_wallet.user_id,
                "balance": new_wallet.balance,
                "is_active": new_wallet.is_active,
                "last_updated": new_wallet.last_updated.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating wallet: {str(e)}"
        )


@router.get("/wallet/{user_id}")
async def get_wallet_balance(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet balance for a user"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found for this user"
            )
        
        return {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "balance": wallet.balance,
            "is_active": wallet.is_active,
            "last_updated": wallet.last_updated.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching wallet: {str(e)}"
        )


@router.post("/wallet/topup/{user_id}")
async def wallet_topup(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: WalletTopupRequest = Body(...)
):
    """Load/Topup wallet with amount and optional remark"""
    try:
        amount = float(data.amount)
        remark = data.remark or ""
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )
        
        # Get wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        
        if not wallet:
            # Create wallet if doesn't exist
            wallet = Wallet(
                user_id=user_id,
                balance=0.0,
                is_active=True,
                last_updated=datetime.utcnow()
            )
            db.add(wallet)
            db.flush()
        
        # Update wallet balance
        wallet.balance += amount
        wallet.last_updated = datetime.utcnow()
        
        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type="credit",
            remark=remark,
            reference_id=f"TOPUP{uuid.uuid4().hex[:8].upper()}",
            balance_after=wallet.balance,
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(wallet)
        
        return {
            "success": True,
            "message": "Wallet topped up successfully",
            "data": {
                "id": wallet.id,
                "user_id": wallet.user_id,
                "balance": wallet.balance,
                "transaction_id": transaction.reference_id,
                "amount_added": amount,
                "remark": remark,
                "last_updated": wallet.last_updated.isoformat()
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error topping up wallet: {str(e)}"
        )


@router.get("/wallet/{user_id}/transactions")
async def get_wallet_transactions(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet transaction history"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found for this user"
            )
        
        # Get transactions with pagination
        transactions = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        ).order_by(
            WalletTransaction.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        total_count = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        ).count()
        
        transaction_list = [
            {
                "id": txn.id,
                "amount": txn.amount,
                "type": txn.transaction_type,
                "reference_id": txn.reference_id,
                "remark": txn.remark,
                "balance_after": txn.balance_after,
                "created_at": txn.created_at.isoformat()
            }
            for txn in transactions
        ]
        
        return {
            "success": True,
            "data": {
                "wallet_id": wallet.id,
                "wallet_balance": wallet.balance,
                "transactions": transaction_list,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transactions: {str(e)}"
        )


# ======================== LEGACY ENDPOINTS (KEPT FOR BACKWARD COMPATIBILITY) ========================

@router.get("/list")
async def get_transactions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent transactions"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            return {"success": True, "data": []}
        
        transactions = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        ).order_by(
            WalletTransaction.created_at.desc()
        ).limit(10).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": txn.id,
                    "amount": txn.amount,
                    "type": txn.transaction_type,
                    "remark": txn.remark,
                    "created_at": txn.created_at.isoformat()
                }
                for txn in transactions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/wallet/balance")
async def get_wallet_balance_legacy(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's wallet balance"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
        
        return {
            "balance": wallet.balance,
            "currency": "INR",
            "last_updated": wallet.last_updated.isoformat(),
            "is_active": wallet.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history")
async def get_transaction_history(
    start_date: str = None,
    end_date: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            return {"success": True, "data": []}
        
        query = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        )
        
        # Add date filters if provided
        if start_date:
            query = query.filter(WalletTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(WalletTransaction.created_at <= end_date)
        
        transactions = query.order_by(WalletTransaction.created_at.desc()).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": txn.id,
                    "amount": txn.amount,
                    "type": txn.transaction_type,
                    "remark": txn.remark,
                    "balance_after": txn.balance_after,
                    "reference_id": txn.reference_id,
                    "created_at": txn.created_at.isoformat()
                }
                for txn in transactions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
