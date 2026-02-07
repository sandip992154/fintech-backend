import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

def test_create_wallet(client, auth_headers):
    response = client.post("/transactions/wallet/create", headers=auth_headers)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "balance" in response.json()

def test_wallet_topup(client, auth_headers):
    data = {
        "amount": 1000.0,
        "payment_method": "upi",
        "reference_id": "TEST123"
    }
    response = client.post(
        "/transactions/wallet/topup",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "transaction_id" in response.json()
    assert "new_balance" in response.json()

def test_wallet_transfer(client, auth_headers, test_user):
    data = {
        "amount": 100.0,
        "to_user_id": test_user["id"],
        "description": "Test transfer"
    }
    response = client.post(
        "/transactions/transfer",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "transaction_id" in response.json()

def test_get_transactions(client, auth_headers):
    response = client.get("/transactions/list", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_wallet_balance(client, auth_headers):
    response = client.get("/transactions/wallet/balance", headers=auth_headers)
    assert response.status_code == 200
    assert "balance" in response.json()

def test_get_transaction_history(client, auth_headers):
    response = client.get(
        "/transactions/history",
        params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
