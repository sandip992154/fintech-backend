from typing import Optional, Dict, Any
import httpx
from datetime import datetime
from fastapi import HTTPException

class AEPSService:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def validate_fingerprint(self, biometric_data: str, aadhaar: str) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/aeps/validate"
        payload = {
            "biometric": biometric_data,
            "aadhaar": aadhaar
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def balance_enquiry(self, biometric_data: str, aadhaar: str, bank_iin: str) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/aeps/balance"
        payload = {
            "biometric": biometric_data,
            "aadhaar": aadhaar,
            "bank_iin": bank_iin
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def cash_withdrawal(
        self,
        biometric_data: str,
        aadhaar: str,
        bank_iin: str,
        amount: float,
        transaction_id: str
    ) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/aeps/withdrawal"
        payload = {
            "biometric": biometric_data,
            "aadhaar": aadhaar,
            "bank_iin": bank_iin,
            "amount": amount,
            "transaction_id": transaction_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

class MATMService:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_device(self, device_id: str) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/matm/initialize"
        payload = {"device_id": device_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def card_transaction(
        self,
        card_data: str,
        amount: float,
        transaction_type: str,
        device_id: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/matm/transaction"
        payload = {
            "card_data": card_data,
            "amount": amount,
            "type": transaction_type,
            "device_id": device_id,
            "transaction_id": transaction_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

class InsuranceService:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_insurance_quotes(
        self,
        insurance_type: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/insurance/quotes"
        payload = {
            "type": insurance_type,
            "customer_data": customer_data
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def purchase_insurance(
        self,
        quote_id: str,
        customer_data: Dict[str, Any],
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/insurance/purchase"
        payload = {
            "quote_id": quote_id,
            "customer_data": customer_data,
            "payment_data": payment_data
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

class PanCardService:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def apply_new_pan(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/pan/apply"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=applicant_data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def check_pan_status(self, application_id: str) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/pan/status/{application_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()

class FastTagService:
    def __init__(self, api_endpoint: str, api_key: str, api_secret: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def recharge_fastag(
        self,
        vehicle_number: str,
        amount: float,
        transaction_id: str
    ) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/fastag/recharge"
        payload = {
            "vehicle_number": vehicle_number,
            "amount": amount,
            "transaction_id": transaction_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def check_balance(self, vehicle_number: str) -> Dict[str, Any]:
        endpoint = f"{self.api_endpoint}/fastag/balance/{vehicle_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
