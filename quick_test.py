#!/usr/bin/env python3
"""
Quick Wallet Topup Test - 2 Minutes to Verify Everything Works
"""

import requests
import json

BACKEND = "http://localhost:8000"
API = f"{BACKEND}/api/v1"

print("\n" + "="*70)
print("  WALLET TOPUP QUICK TEST")
print("="*70 + "\n")

# Step 1: Login
print("📝 Step 1: Getting Authentication Token...")
try:
    resp = requests.post(f"{API}/auth/superadmin/login", json={
        "username": "superadmin",
        "password": "superadmin@123"
    })
    
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print(f"✅ Login successful\n   Token: {token[:30]}...\n")
    else:
        print(f"❌ Login failed: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("   Make sure backend is running: python main.py")
    exit(1)

# Step 2: Add Funds
print("💰 Step 2: Adding ₹200 to wallet...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    resp = requests.post(f"{API}/transactions/wallet/topup/1", 
        json={"amount": 200.0, "remark": "Quick test"},
        headers=headers
    )
    
    if resp.status_code == 200 and resp.json()["success"]:
        data = resp.json()["data"]
        print(f"✅ Topup successful!")
        print(f"   Amount: ₹{data['amount_added']}")
        print(f"   New Balance: ₹{data['balance']}")
        print(f"   Transaction ID: {data['transaction_id']}\n")
    else:
        print(f"❌ Topup failed: {resp.status_code}")
        print(f"   Response: {json.dumps(resp.json(), indent=2)}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

# Step 3: Verify Balance
print("🔍 Step 3: Verifying wallet balance...")
try:
    resp = requests.get(f"{API}/transactions/wallet/1", headers=headers)
    
    if resp.status_code == 200:
        balance = resp.json()["balance"]
        print(f"✅ Current Balance: ₹{balance}\n")
    else:
        print(f"❌ Could not fetch balance: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

# Step 4: Transaction History
print("📋 Step 4: Transaction History...")
try:
    resp = requests.get(
        f"{API}/transactions/wallet/1/transactions?limit=5&offset=0",
        headers=headers
    )
    
    if resp.status_code == 200:
        txns = resp.json()["data"]["transactions"]
        print(f"✅ Found {len(txns)} transaction(s):\n")
        
        for i, txn in enumerate(txns[:2], 1):  # Show first 2
            print(f"   Transaction {i}:")
            print(f"     Type: {txn['type']}")
            print(f"     Amount: ₹{txn['amount']}")
            print(f"     Remark: {txn['remark']}")
            print(f"     Balance After: ₹{txn['balance_after']}")
            print()
    else:
        print(f"❌ Could not fetch history: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

print("="*70)
print("  ✅ ALL TESTS PASSED - FULLY WORKING!")
print("="*70 + "\n")
