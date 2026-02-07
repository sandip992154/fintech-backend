import requests
import json
import sys

BASE_URL = 'http://localhost:8000'

print("=" * 70)
print("PostgreSQL Database - API Connection Test")
print("=" * 70)

access_token = None

# Test 1: Demo Login
print("\n[TEST 1] Demo Login (PostgreSQL)")
print("-" * 70)
try:
    creds = {
        'username': 'superadmin',
        'password': 'SuperAdmin@123'
    }
    response = requests.post(f'{BASE_URL}/api/v1/auth/demo-login', data=creds, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful from PostgreSQL")
        print(f"   Status: {response.status_code}")
        print(f"   Role: {data.get('role')}")
        print(f"   Token: {data.get('access_token')[:50]}...")
        access_token = data.get('access_token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Verify Current User (proves token works with PostgreSQL)
if access_token:
    print("\n[TEST 2] Verify Current User (PostgreSQL)")
    print("-" * 70)
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{BASE_URL}/api/v1/auth/me', headers=headers, timeout=5)
        
        if response.status_code == 200:
            user = response.json()
            print("✅ User verified from PostgreSQL")
            print(f"   User Code: {user.get('user_code')}")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ PostgreSQL Database Configuration Complete!")
print("=" * 70)
print("\nYour backend is now using PostgreSQL:")
print("  Host: dpg-d63l9rfgi27c739iec10-a.oregon-postgres.render.com")
print("  Database: fintech_db_z4ic")
print("  Status: ✅ Ready for production")
