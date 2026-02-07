from typing import Optional, Dict, Any
import httpx
import json
from datetime import datetime
from fastapi import HTTPException

class ServiceIntegration:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_endpoint}/{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service provider error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Service request failed: {str(e)}"
            )

class RechargeService(ServiceIntegration):
    async def validate_number(self, mobile_number: str, operator: str) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="validate/mobile",
            data={
                "mobile_number": mobile_number,
                "operator": operator
            }
        )
    
    async def get_plans(self, operator: str, circle: str) -> Dict[str, Any]:
        return await self._make_request(
            method="GET",
            endpoint="plans",
            params={
                "operator": operator,
                "circle": circle
            }
        )
    
    async def process_recharge(
        self,
        mobile_number: str,
        amount: float,
        operator: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="recharge",
            data={
                "mobile_number": mobile_number,
                "amount": amount,
                "operator": operator,
                "transaction_id": transaction_id
            }
        )

class BillPaymentService(ServiceIntegration):
    async def fetch_bill(
        self,
        consumer_id: str,
        provider: str,
        payment_type: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="fetch/bill",
            data={
                "consumer_id": consumer_id,
                "provider": provider,
                "type": payment_type
            }
        )
    
    async def pay_bill(
        self,
        bill_id: str,
        amount: float,
        transaction_id: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="pay/bill",
            data={
                "bill_id": bill_id,
                "amount": amount,
                "transaction_id": transaction_id
            }
        )

class MoneyTransferService(ServiceIntegration):
    async def validate_account(
        self,
        bank_code: str,
        account_number: str,
        ifsc: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="validate/account",
            data={
                "bank_code": bank_code,
                "account_number": account_number,
                "ifsc": ifsc
            }
        )
    
    async def transfer_money(
        self,
        bank_code: str,
        account_number: str,
        ifsc: str,
        amount: float,
        transaction_id: str,
        purpose: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            method="POST",
            endpoint="transfer",
            data={
                "bank_code": bank_code,
                "account_number": account_number,
                "ifsc": ifsc,
                "amount": amount,
                "transaction_id": transaction_id,
                "purpose": purpose
            }
        )
