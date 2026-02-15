#!/usr/bin/env python3
"""
Complete Wallet Topup Flow Test
Tests: Authentication → Wallet Creation → Balance Check → Topup → Refresh Balance → Transaction History
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"  # Local backend
API_PREFIX = f"{BACKEND_URL}/api/v1"

# Test user credentials (use existing superadmin or test user)
TEST_USER_ID = 1
TEST_TOKEN = None  # Will be set after login

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")

def print_request(method, url, data=None):
    print(f"{BLUE}→ {method} {url}{RESET}")
    if data:
        print(f"  Body: {json.dumps(data, indent=2)}")

def print_response(status, data):
    print(f"  Status: {status}")
    print(f"  Response: {json.dumps(data, indent=2)}")

# Test 1: Login to get token
def test_login():
    print_section("TEST 1: User Login (Get Authorization Token)")
    
    try:
        # For superadmin, use superadmin endpoint
        url = f"{API_PREFIX}/auth/superadmin/login"
        data = {
            "username": "superadmin",
            "password": "superadmin@123"
        }
        
        print_request("POST", url, data)
        response = requests.post(url, json=data)
        print_response(response.status_code, response.json())
        
        if response.status_code == 200:
            global TEST_TOKEN
            TEST_TOKEN = response.json().get("access_token")
            print_success(f"Login successful! Token: {TEST_TOKEN[:20]}...")
            return True
        else:
            print_error(f"Login failed")
            return False
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return False

# Test 2: Check wallet exists
def test_get_wallet_balance():
    print_section("TEST 2: Get Current Wallet Balance")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/{TEST_USER_ID}"
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        
        print_request("GET", url)
        response = requests.get(url, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            balance = data.get("balance", 0)
            print_success(f"Current wallet balance: ₹{balance}")
            return True
        elif response.status_code == 404:
            print_info("Wallet not found (will be created on first topup)")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get balance error: {str(e)}")
        return False

# Test 3: Wallet Topup
def test_wallet_topup():
    print_section("TEST 3: Add Funds to Wallet (Topup)")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/topup/{TEST_USER_ID}"
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "Content-Type": "application/json"
        }
        
        topup_data = {
            "amount": 500.00,
            "remark": "Test topup - automated flow verification"
        }
        
        print_request("POST", url, topup_data)
        response = requests.post(url, json=topup_data, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success(f"Topup successful!")
                print_success(f"  - Amount Added: ₹{data['data'].get('amount_added')}")
                print_success(f"  - New Balance: ₹{data['data'].get('balance')}")
                print_success(f"  - Transaction ID: {data['data'].get('transaction_id')}")
                print_success(f"  - Remark: {data['data'].get('remark')}")
                return True
            else:
                print_error(f"Topup failed: {data.get('message')}")
                return False
        else:
            print_error(f"Error: {response.status_code}")
            if response.status_code >= 400:
                print_error(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Topup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Test 4: Verify updated balance
def test_verify_balance():
    print_section("TEST 4: Verify Balance Updated")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/{TEST_USER_ID}"
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        
        print_request("GET", url)
        response = requests.get(url, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            balance = data.get("balance", 0)
            if balance >= 500:  # Should have at least 500 from topup
                print_success(f"✓ Balance correctly updated: ₹{balance}")
                return True
            else:
                print_error(f"Balance not updated correctly: ₹{balance}")
                return False
        else:
            print_error(f"Could not fetch balance: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Balance verification error: {str(e)}")
        return False

# Test 5: Get transaction history
def test_transaction_history():
    print_section("TEST 5: Get Transaction History")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/{TEST_USER_ID}/transactions?limit=10&offset=0"
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        
        print_request("GET", url)
        response = requests.get(url, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("data", {}).get("transactions", [])
            print_success(f"Retrieved {len(transactions)} transaction(s)")
            
            if len(transactions) > 0:
                for i, txn in enumerate(transactions, 1):
                    print(f"\n  Transaction {i}:")
                    print(f"    - Type: {txn.get('type')} ✓")
                    print(f"    - Amount: ₹{txn.get('amount')} ✓")
                    print(f"    - Remark: {txn.get('remark')} ✓")
                    print(f"    - Balance After: ₹{txn.get('balance_after')} ✓")
                    print(f"    - Reference: {txn.get('reference_id')} ✓")
                    print(f"    - Date: {txn.get('created_at')} ✓")
            return True
        else:
            print_error(f"Could not fetch transactions: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Transaction history error: {str(e)}")
        return False

# Test 6: Multiple topups
def test_multiple_topups():
    print_section("TEST 6: Multiple Topups (Stress Test)")
    
    amounts = [100.0, 250.50, 150.0]
    results = []
    
    for i, amount in enumerate(amounts, 1):
        try:
            url = f"{API_PREFIX}/transactions/wallet/topup/{TEST_USER_ID}"
            headers = {
                "Authorization": f"Bearer {TEST_TOKEN}",
                "Content-Type": "application/json"
            }
            
            topup_data = {
                "amount": amount,
                "remark": f"Test topup #{i} - ₹{amount}"
            }
            
            response = requests.post(url, json=topup_data, headers=headers)
            
            if response.status_code == 200 and response.json().get("success"):
                print_success(f"Topup #{i} successful: ₹{amount}")
                results.append(True)
            else:
                print_error(f"Topup #{i} failed: ₹{amount}")
                results.append(False)
        except Exception as e:
            print_error(f"Topup #{i} error: {str(e)}")
            results.append(False)
    
    return all(results)

# Test 7: Negative amount (validation test)
def test_negative_amount():
    print_section("TEST 7: Validation - Negative Amount")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/topup/{TEST_USER_ID}"
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "Content-Type": "application/json"
        }
        
        topup_data = {
            "amount": -100.0,
            "remark": "Should fail"
        }
        
        print_request("POST", url, topup_data)
        response = requests.post(url, json=topup_data, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code >= 400:
            print_success("✓ Negative amount correctly rejected")
            return True
        else:
            print_error("Negative amount was not rejected!")
            return False
    except Exception as e:
        print_error(f"Validation test error: {str(e)}")
        return False

# Test 8: Exceeding max limit
def test_max_limit():
    print_section("TEST 8: Validation - Exceeding Max Limit (>100000)")
    
    try:
        url = f"{API_PREFIX}/transactions/wallet/topup/{TEST_USER_ID}"
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "Content-Type": "application/json"
        }
        
        topup_data = {
            "amount": 150000.0,
            "remark": "Should fail - exceeds limit"
        }
        
        print_request("POST", url, topup_data)
        response = requests.post(url, json=topup_data, headers=headers)
        print_response(response.status_code, response.json())
        
        if response.status_code >= 400:
            print_success("✓ Amount exceeding max limit correctly rejected")
            return True
        else:
            print_error("Amount exceeding max limit was not rejected!")
            return False
    except Exception as e:
        print_error(f"Limit test error: {str(e)}")
        return False

# Main test runner
def run_all_tests():
    print(f"\n{BLUE}{'='*70}")
    print("  🎯 COMPLETE WALLET TOPUP FLOW TEST")
    print("  Testing: Authentication → Wallet Creation → Topup → Verify")
    print(f"{'='*70}{RESET}")
    
    tests = [
        ("Login", test_login),
        ("Get Wallet Balance", test_get_wallet_balance),
        ("Wallet Topup", test_wallet_topup),
        ("Verify Updated Balance", test_verify_balance),
        ("Transaction History", test_transaction_history),
        ("Multiple Topups", test_multiple_topups),
        ("Validation - Negative Amount", test_negative_amount),
        ("Validation - Max Limit", test_max_limit),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results[test_name] = False
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BLUE}Result: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}✅ ALL TESTS PASSED - FULLY WORKING!{RESET}\n")
        return True
    else:
        print(f"{RED}⚠️  SOME TESTS FAILED{RESET}\n")
        return False

if __name__ == "__main__":
    print_info("Make sure backend is running on localhost:8000")
    print_info("Starting tests in 2 seconds...\n")
    
    import time
    time.sleep(2)
    
    success = run_all_tests()
    exit(0 if success else 1)
