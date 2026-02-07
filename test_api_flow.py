import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend-api'))

BASE_URL = 'http://localhost:8000'

print('🔐 Testing Complete Login + Schemes API Flow\n')

# Step 1: Demo Login
print('1️⃣ Testing Demo Login...')
try:
    demo_creds = {
        'username': 'superadmin',
        'password': 'SuperAdmin@123'
    }
    response = requests.post(f'{BASE_URL}/api/v1/auth/demo-login', data=demo_creds)
    if response.status_code == 200:
        login_data = response.json()
        access_token = login_data.get('access_token')
        token_type = login_data.get('token_type')
        user_code = login_data.get('user_code')
        print('✅ Login successful')
        print(f'   Token: {access_token[:50]}...')
        print(f'   Type: {token_type}')
        print(f'   User: {user_code}')
    else:
        print(f'❌ Login failed: {response.status_code}')
        print(f'   Response: {response.text}')
        exit(1)
except Exception as e:
    print(f'❌ Connection error: {e}')
    exit(1)

# Step 2: Get Schemes with token
print('\n2️⃣ Testing Schemes API with token...')
try:
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{BASE_URL}/api/v1/schemes?skip=0&limit=10', headers=headers)
    print(f'   Status: {response.status_code}')

    if response.status_code == 200:
        schemes = response.json()
        print('✅ Schemes API successful')
        if isinstance(schemes, dict):
            items = schemes.get('items', [])
            print(f'   Found {len(items)} schemes')
            for idx, scheme in enumerate(items[:3], 1):
                scheme_name = scheme.get('name', 'Unknown')
                scheme_id = scheme.get('id')
                print(f'   {idx}. {scheme_name} (ID: {scheme_id})')
            if len(items) > 3:
                remaining = len(items) - 3
                print(f'   ... and {remaining} more')
        else:
            print(f'   Response type: {type(schemes).__name__}')
            if isinstance(schemes, list):
                print(f'   Count: {len(schemes)}')
    else:
        print(f'❌ Schemes API failed: {response.status_code}')
        print(f'   Response: {response.text[:200]}')
except Exception as e:
    print(f'❌ Connection error: {e}')

print('\n✅ Test Complete!')
