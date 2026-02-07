import pytest
from fastapi.testclient import TestClient

def test_aeps_balance_enquiry(client, auth_headers):
    data = {
        "aadhaar": "123456789012",
        "biometric_data": "test_biometric_data",
        "bank_iin": "123456"
    }
    response = client.post(
        "/additional-services/aeps/balance-enquiry",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "balance" in response.json()

def test_aeps_cash_withdrawal(client, auth_headers):
    data = {
        "aadhaar": "123456789012",
        "biometric_data": "test_biometric_data",
        "bank_iin": "123456",
        "amount": 1000.0
    }
    response = client.post(
        "/additional-services/aeps/cash-withdrawal",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "transaction_id" in response.json()

def test_matm_initialize(client, auth_headers):
    data = {
        "device_id": "MATM123456"
    }
    response = client.post(
        "/additional-services/matm/initialize",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "status" in response.json()

def test_matm_transaction(client, auth_headers):
    data = {
        "card_data": "test_card_data",
        "amount": 1000.0,
        "transaction_type": "withdrawal",
        "device_id": "MATM123456"
    }
    response = client.post(
        "/additional-services/matm/transaction",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "transaction_id" in response.json()

def test_insurance_get_quotes(client, auth_headers):
    data = {
        "insurance_type": "life",
        "customer_data": {
            "name": "Test Customer",
            "age": 30,
            "coverage_amount": 1000000
        }
    }
    response = client.post(
        "/additional-services/insurance/get-quotes",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "quotes" in response.json()

def test_pan_card_application(client, auth_headers):
    data = {
        "applicant_data": {
            "name": "Test Applicant",
            "father_name": "Test Father",
            "dob": "1990-01-01",
            "mobile": "9876543210",
            "email": "test@example.com"
        }
    }
    response = client.post(
        "/additional-services/pan/apply",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "application_number" in response.json()

def test_fastag_recharge(client, auth_headers):
    data = {
        "vehicle_number": "MH12AB1234",
        "amount": 500.0
    }
    response = client.post(
        "/additional-services/fastag/recharge",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "transaction_id" in response.json()
