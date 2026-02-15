from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from decimal import Decimal, InvalidOperation
from datetime import datetime
import uuid
import logging

from database.database import get_db
from services.models.transaction_models import (
    Transaction, Wallet, WalletTransaction,
    TransactionStatus, TransactionType
)
from services.models.models import User
from services.schemas.transaction_schemas import (
    TransactionCreate, TransactionOut, WalletOut,
    WalletTransactionCreate, WalletTransactionOut, WalletTopupRequest
)
from services.auth.auth import get_current_user
from utils.error_handlers import APIErrorResponse, handle_database_exceptions, validate_required_fields, validate_user_permissions

router = APIRouter(prefix="/transactions", tags=["Transactions"])
# ⚠️ NOTE: This router is included with /api/v1 prefix in main.py
# So the /transactions prefix here creates /api/v1/transactions/*
logger = logging.getLogger(__name__)

# Wallet Operations
@router.get("/wallet/{user_id}", response_model=WalletOut)
async def get_wallet_balance(user_id: int, db: Session = Depends(get_db)):
    """
    Get wallet balance for a specific user with comprehensive error handling.
    """
    logger.info(f"Wallet balance request for user ID: {user_id}")
    
    try:
        # Validate user ID
        if not user_id or user_id <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid user ID provided",
                details={
                    "provided_user_id": user_id,
                    "action": "provide_valid_positive_user_id"
                },
                field="user_id"
            )

        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            logger.info(f"Wallet not found for user ID: {user_id}")
            raise APIErrorResponse.not_found_error(
                message="Wallet not found for this user",
                details={
                    "user_id": user_id,
                    "action": "wallet_will_be_created_on_first_transaction"
                },
                resource_type="wallet"
            )

        logger.info(f"Wallet balance retrieved for user {user_id}: {wallet.balance}")
        return wallet

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving wallet for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to retrieve wallet balance",
            details={
                "error": "database_query_failed",
                "user_id": user_id,
                "action": "try_again_or_contact_support"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise

@router.post("/wallet/create", status_code=201)
async def create_wallet_for_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new wallet for a user.
    
    Returns:
        201: Wallet created successfully with wallet details
        400: Invalid user ID or wallet already exists
        401: Authentication required
        500: Server error
    """
    logger.info(f"Wallet creation request by user {current_user.id}")
    
    try:
        user_id = user_data.get("user_id") or current_user.id
        
        # Validate user ID
        if not user_id or user_id <= 0:
            logger.warning(f"Invalid user ID provided: {user_id}")
            raise HTTPException(
                status_code=400,
                detail="User ID must be a positive integer"
            )
        
        # Check if wallet already exists
        existing_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if existing_wallet:
            logger.info(f"Wallet already exists for user {user_id}")
            raise HTTPException(
                status_code=400,
                detail="Wallet already exists for this user"
            )
        
        # Create new wallet
        new_wallet = Wallet(
            user_id=user_id,
            balance=0.0,
            is_active=True
        )
        
        db.add(new_wallet)
        db.commit()
        db.refresh(new_wallet)
        
        logger.info(f"Wallet created successfully for user {user_id} with ID {new_wallet.id}")
        
        return {
            "success": True,
            "message": "Wallet created successfully",
            "status": "wallet_created",
            "wallet": {
                "id": new_wallet.id,
                "user_id": new_wallet.user_id,
                "balance": float(new_wallet.balance),
                "is_active": new_wallet.is_active,
                "created_at": new_wallet.last_updated.isoformat() if hasattr(new_wallet.last_updated, 'isoformat') else str(new_wallet.last_updated)
            }
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating wallet: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Wallet already exists for this user or invalid data"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating wallet: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database error while creating wallet. Please try again."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating wallet: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating wallet"
        )

@router.post("/wallet/topup/{user_id}")
async def topup_wallet(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: WalletTopupRequest = Body(...)
):
    """
    Top up user wallet with comprehensive validation and error handling.
    """
    try:
        # Convert to float immediately to avoid type conflicts
        amount_float = float(data.amount)
        remark = data.remark or ""
        
        logger.info(f"Wallet topup request for user {user_id}, amount: {amount_float}, remark: {remark}")
        
        # Validate user ID
        if not user_id or user_id <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid user ID provided",
                details={
                    "provided_user_id": user_id,
                    "action": "provide_valid_positive_user_id"
                },
                field="user_id"
            )

        # Validate amount
        if amount_float <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid topup amount",
                details={
                    "provided_amount": str(amount_float),
                    "minimum_amount": "0.01",
                    "action": "provide_positive_amount"
                },
                field="amount"
            )

        # Check maximum topup limit
        if amount_float > 100000.00:  # 1 lakh maximum
            raise APIErrorResponse.business_rule_error(
                message="Topup amount exceeds maximum limit",
                details={
                    "requested_amount": str(amount_float),
                    "maximum_allowed": "100000.00",
                    "action": "reduce_topup_amount"
                },
                rule="maximum_topup_limit"
            )

        # Get or create wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            logger.info(f"Creating new wallet for user {user_id}")
            wallet = Wallet(user_id=user_id, balance=0.0, is_active=True)
            db.add(wallet)
            db.flush()
            db.refresh(wallet)

        # Calculate new balance
        current_balance = float(wallet.balance) if wallet.balance else 0.0
        new_balance = current_balance + amount_float
        
        # Check balance limit after topup
        if new_balance > 500000.00:  # 5 lakh maximum balance
            raise APIErrorResponse.business_rule_error(
                message="Topup would exceed maximum wallet balance",
                details={
                    "current_balance": str(current_balance),
                    "topup_amount": str(amount_float),
                    "resulting_balance": str(new_balance),
                    "maximum_balance": "500000.00",
                    "action": "reduce_topup_amount_or_use_funds_first"
                },
                rule="maximum_wallet_balance"
            )

        # Create wallet transaction record
        reference_id = f"TOPUP-{uuid.uuid4().hex[:8].upper()}"
        wallet_txn = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount_float,
            transaction_type="credit",
            reference_id=reference_id,
            remark=remark,
            balance_after=new_balance
        )
        
        # Update wallet balance
        wallet.balance = new_balance
        wallet.last_updated = datetime.utcnow()
        
        db.add(wallet_txn)
        db.flush()
        db.commit()
        db.refresh(wallet)
        
        logger.info(f"✅ Wallet topup successful for user {user_id}: ₹{amount_float} -> new balance: ₹{wallet.balance}")
        
        return {
            "success": True,
            "message": "Wallet topped up successfully",
            "data": {
                "id": wallet.id,
                "user_id": wallet.user_id,
                "balance": float(wallet.balance),
                "transaction_id": reference_id,
                "amount_added": amount_float,
                "remark": remark,
                "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None
            }
        }

    except APIErrorResponse as e:
        logger.error(f"API Error during wallet topup for user {user_id}: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during wallet topup for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "database_error",
                "message": "Failed to complete wallet topup",
                "details": {
                    "error": "database_transaction_failed",
                    "user_id": user_id,
                    "action": "try_again_or_contact_support"
                }
            }
        )
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.error(f"Invalid data type during wallet topup for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": "Invalid amount format",
                "details": {
                    "provided_amount": str(data.amount),
                    "error": "invalid_number_format",
                    "action": "provide_valid_positive_number"
                }
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during wallet topup for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "message": "An unexpected error occurred during wallet topup",
                "details": {
                    "error": "unexpected_error",
                    "user_id": user_id,
                    "action": "contact_support"
                }
            }
        )

@router.get("/wallet/{user_id}/transactions")
async def get_wallet_transactions(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet transaction history with pagination"""
    logger.info(f"Wallet transactions request for user {user_id}, limit: {limit}, offset: {offset}")
    
    try:
        # Validate user ID
        if not user_id or user_id <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid user ID provided",
                details={
                    "provided_user_id": user_id,
                    "action": "provide_valid_positive_user_id"
                },
                field="user_id"
            )
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        
        if not wallet:
            raise APIErrorResponse.not_found_error(
                message="Wallet not found for this user",
                details={
                    "user_id": user_id,
                    "action": "create_wallet_first"
                },
                resource_type="wallet"
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
                "amount": float(txn.amount),
                "type": txn.transaction_type,
                "reference_id": txn.reference_id,
                "remark": txn.remark,
                "balance_after": float(txn.balance_after),
                "created_at": txn.created_at.isoformat() if txn.created_at else None
            }
            for txn in transactions
        ]
        
        logger.info(f"Retrieved {len(transaction_list)} transactions for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "wallet_id": wallet.id,
                "wallet_balance": float(wallet.balance),
                "transactions": transaction_list,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        }
        
    except APIErrorResponse as e:
        logger.error(f"API error retrieving transactions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving wallet transactions for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to retrieve wallet transactions",
            details={
                "error": "database_query_failed",
                "user_id": user_id,
                "action": "try_again_or_contact_support"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving wallet transactions for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred while retrieving transactions",
            details={
                "error": "unexpected_transaction_error",
                "user_id": user_id,
                "action": "contact_support"
            }
        )

@router.post("/transfer/{from_user_id}/{to_user_id}")
async def transfer_funds(
    from_user_id: int,
    to_user_id: int,
    amount: Decimal,
    db: Session = Depends(get_db)
):
    # Get source wallet
    from_wallet = db.query(Wallet).filter(Wallet.user_id == from_user_id).first()
    if not from_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source wallet not found"
        )
    
    # Check balance
    if from_wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient balance"
        )
    
    # Get destination wallet
    to_wallet = db.query(Wallet).filter(Wallet.user_id == to_user_id).first()
    if not to_wallet:
        to_wallet = Wallet(user_id=to_user_id, balance=Decimal("0.00"))
        db.add(to_wallet)
        db.commit()
        db.refresh(to_wallet)

    # Generate reference ID
    ref_id = f"TXN-{uuid.uuid4().hex[:8]}"

    try:
        # Create debit transaction
        debit_txn = WalletTransaction(
            wallet_id=from_wallet.id,
            amount=amount,
            transaction_type="debit",
            reference_id=ref_id,
            balance_after=from_wallet.balance - amount
        )
        
        # Create credit transaction
        credit_txn = WalletTransaction(
            wallet_id=to_wallet.id,
            amount=amount,
            transaction_type="credit",
            reference_id=ref_id,
            balance_after=to_wallet.balance + amount
        )
        
        # Update balances
        from_wallet.balance -= amount
        to_wallet.balance += amount
        
        db.add_all([debit_txn, credit_txn])
        db.commit()
        
        return {
            "message": "Transfer successful",
            "transaction_id": ref_id,
            "from_balance": str(from_wallet.balance),
            "to_balance": str(to_wallet.balance)
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer failed due to database error"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer failed"
        )

# Transaction Operations
@router.post("/create", response_model=TransactionOut)
async def create_transaction(
    transaction: TransactionCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    # Generate reference ID
    ref_id = f"{transaction.transaction_type}-{uuid.uuid4().hex[:8]}"
    
    db_transaction = Transaction(
        user_id=user_id,
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        status=TransactionStatus.PENDING,
        reference_id=ref_id,
        description=transaction.description,
        provider_id=transaction.provider_id
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@router.get("/history/{user_id}", response_model=List[TransactionOut])
async def get_transaction_history(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction)\
        .filter(Transaction.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return transactions

@router.get("/status/{transaction_id}", response_model=TransactionOut)
async def get_transaction_status(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction
