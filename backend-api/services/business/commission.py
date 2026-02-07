from typing import Any, Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from services.models.models import User, Role
from services.models.transaction_models import CommissionStructure, Transaction, Wallet, WalletTransaction
import uuid

class CommissionCalculator:
    def __init__(self, db: Session):
        self.db = db
    
    def get_commission_structure(
        self,
        role_id: int,
        service_id: int
    ) -> Optional[CommissionStructure]:
        return self.db.query(CommissionStructure).filter(
            CommissionStructure.role_id == role_id,
            CommissionStructure.service_id == service_id,
            CommissionStructure.is_active == True
        ).first()
    
    def calculate_commission(
        self,
        amount: Decimal,
        role_id: int,
        service_id: int
    ) -> Dict[str, Decimal]:
        commission_structure = self.get_commission_structure(role_id, service_id)
        if not commission_structure:
            raise HTTPException(
                status_code=404,
                detail="Commission structure not found"
            )
        
        if amount < commission_structure.min_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Amount should be greater than {commission_structure.min_amount}"
            )
        
        if commission_structure.max_amount and amount > commission_structure.max_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Amount should be less than {commission_structure.max_amount}"
            )
        
        commission = (amount * Decimal(str(commission_structure.commission_percentage))) / 100
        charges = (amount * Decimal(str(commission_structure.charge_percentage))) / 100
        
        return {
            "commission": commission,
            "charges": charges,
            "net_commission": commission - charges
        }
    
    async def process_commission(
        self,
        transaction_id: int,
        amount: Decimal,
        user_id: int,
        service_id: int
    ) -> Dict[str, Any]:
        # Get user and their role
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.role_id:
            raise HTTPException(
                status_code=404,
                detail="User or role not found"
            )
        
        # Calculate commission
        commission_details = self.calculate_commission(
            amount=amount,
            role_id=user.role_id,
            service_id=service_id
        )
        
        # Get or create user's wallet
        wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            wallet = Wallet(user_id=user_id, balance=0)
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        
        # Create commission transaction
        commission_txn = Transaction(
            user_id=user_id,
            transaction_type="commission",
            amount=commission_details["net_commission"],
            status="success",
            reference_id=f"COM-{uuid.uuid4().hex[:8]}",
            description=f"Commission for transaction {transaction_id}",
            provider_id=service_id
        )
        self.db.add(commission_txn)
        
        # Update wallet balance
        wallet_txn = WalletTransaction(
            wallet_id=wallet.id,
            amount=commission_details["net_commission"],
            transaction_type="credit",
            reference_id=commission_txn.reference_id,
            balance_after=wallet.balance + commission_details["net_commission"]
        )
        self.db.add(wallet_txn)
        
        wallet.balance += commission_details["net_commission"]
        
        self.db.commit()
        
        return {
            "transaction_id": commission_txn.id,
            "reference_id": commission_txn.reference_id,
            "amount": commission_details["net_commission"],
            "new_balance": wallet.balance
        }
    
    async def process_hierarchy_commission(
        self,
        transaction_id: int,
        amount: Decimal,
        user_id: int,
        service_id: int
    ) -> List[Dict[str, Any]]:
        """Process commission for entire hierarchy"""
        results = []
        current_user = self.db.query(User).filter(User.id == user_id).first()
        
        while current_user and current_user.role_id:
            try:
                commission_result = await self.process_commission(
                    transaction_id=transaction_id,
                    amount=amount,
                    user_id=current_user.id,
                    service_id=service_id
                )
                results.append({
                    "user_id": current_user.id,
                    "role_id": current_user.role_id,
                    **commission_result
                })
            except HTTPException:
                # Skip if no commission structure found for this role
                pass
                
            # Move up the hierarchy (implement your hierarchy logic here)
            # For example: get parent user based on your business logic
            current_user = None  # Replace with your hierarchy logic
        
        return results
