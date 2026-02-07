from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from decimal import Decimal, InvalidOperation
import uuid
import logging

from database.database import get_db
from services.models.transaction_models import (
    Transaction, Wallet, WalletTransaction,
    TransactionStatus, TransactionType
)
from services.schemas.transaction_schemas import (
    TransactionCreate, TransactionOut, WalletOut,
    WalletTransactionCreate, WalletTransactionOut
)
from utils.error_handlers import APIErrorResponse, handle_database_exceptions, validate_required_fields, validate_user_permissions

router = APIRouter(prefix="/transactions", tags=["Transactions"])
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
    except Exception as e:
        logger.error(f"Unexpected error retrieving wallet for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred while retrieving wallet balance",
            details={
                "error": "unexpected_wallet_error",
                "user_id": user_id,
                "action": "contact_support"
            }
        )

@router.post("/wallet/topup/{user_id}")
async def topup_wallet(
    user_id: int,
    amount: Decimal,
    db: Session = Depends(get_db)
):
    """
    Top up user wallet with comprehensive validation and error handling.
    """
    logger.info(f"Wallet topup request for user {user_id}, amount: {amount}")
    
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

        # Validate amount
        if not amount or amount <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid topup amount",
                details={
                    "provided_amount": str(amount),
                    "minimum_amount": "0.01",
                    "action": "provide_positive_amount"
                },
                field="amount"
            )

        # Check maximum topup limit
        max_topup = Decimal("100000.00")  # 1 lakh maximum
        if amount > max_topup:
            raise APIErrorResponse.business_rule_error(
                message="Topup amount exceeds maximum limit",
                details={
                    "requested_amount": str(amount),
                    "maximum_allowed": str(max_topup),
                    "action": "reduce_topup_amount"
                },
                rule="maximum_topup_limit"
            )

        # Get or create wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            logger.info(f"Creating new wallet for user {user_id}")
            wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
            db.add(wallet)
            db.commit()
            db.refresh(wallet)

        # Check balance limit after topup
        max_balance = Decimal("500000.00")  # 5 lakh maximum balance
        new_balance = wallet.balance + amount
        if new_balance > max_balance:
            raise APIErrorResponse.business_rule_error(
                message="Topup would exceed maximum wallet balance",
                details={
                    "current_balance": str(wallet.balance),
                    "topup_amount": str(amount),
                    "resulting_balance": str(new_balance),
                    "maximum_balance": str(max_balance),
                    "action": "reduce_topup_amount_or_use_funds_first"
                },
                rule="maximum_wallet_balance"
            )

        # Create wallet transaction record
        reference_id = f"TOPUP-{uuid.uuid4().hex[:8].upper()}"
        wallet_txn = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type="credit",
            reference_id=reference_id,
            balance_after=new_balance
        )
        
        # Update wallet balance
        wallet.balance = new_balance
        
        db.add(wallet_txn)
        db.commit()
        db.refresh(wallet)
        
        logger.info(f"Wallet topup successful for user {user_id}: {amount} -> balance: {wallet.balance}")
        return {
            "message": "Wallet topped up successfully",
            "status": "success",
            "user_id": user_id,
            "topup_amount": str(amount),
            "new_balance": str(wallet.balance),
            "transaction_id": reference_id,
            "timestamp": wallet_txn.created_at
        }

    except (InvalidOperation, ValueError) as e:
        logger.error(f"Invalid decimal amount for topup: {amount}")
        raise APIErrorResponse.validation_error(
            message="Invalid amount format",
            details={
                "provided_amount": str(amount),
                "error": "invalid_decimal_format",
                "action": "provide_valid_decimal_amount"
            },
            field="amount"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during wallet topup for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to complete wallet topup",
            details={
                "error": "database_transaction_failed",
                "user_id": user_id,
                "amount": str(amount),
                "action": "try_again_or_contact_support"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during wallet topup for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred during wallet topup",
            details={
                "error": "unexpected_topup_error",
                "user_id": user_id,
                "amount": str(amount),
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
