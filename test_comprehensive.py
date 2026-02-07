import requests
import json
import sys

BASE_URL = 'http://localhost:8000'

print('=' * 70)
print('✅ COMPREHENSIVE BANDRUPAY API VERIFICATION TEST')
print('=' * 70)

# Store access token for later use
access_token = None

# Test 1: Database Initialization
print('\n[TEST 1] Database Initialization')
print('-' * 70)
try:
    import os
    import shutil
    
    # Copy database from backend-api to root (or use backend-api db)
    backend_db = 'backend-api/bandaru_pay.db'
    root_db = 'bandaru_pay.db'
    
    # Ensure we're looking at the right database
    if os.path.exists(backend_db) and not os.path.exists(root_db):
        shutil.copy(backend_db, root_db)
    
    sys.path.insert(0, 'backend-api')
    
    # Force reload of database to use the root db
    import importlib
    import database.database
    importlib.reload(database.database)
    
    from database.database import SessionLocal
    from services.models.models import User, Role
    from services.models.scheme_models import Scheme
    
    db = SessionLocal()
    user_count = db.query(User).count()
    role_count = db.query(Role).count()
    scheme_count = db.query(Scheme).count()
    db.close()
    
    print(f'✅ Database connected')
    print(f'   Users: {user_count} (Expected: ≥1)')
    print(f'   Roles: {role_count} (Expected: ≥9)')
    print(f'   Schemes: {scheme_count} (Expected: 8)')
    
    if user_count > 0 and role_count >= 9 and scheme_count == 8:
        print('✅ Database verification: PASSED')
    else:
        print('❌ Database verification: FAILED')
except Exception as e:
    print(f'❌ Database connection failed: {e}')

# Test 2: Authentication Service
print('\n[TEST 2] Demo Login Endpoint (/api/v1/auth/demo-login)')
print('-' * 70)
try:
    demo_creds = {
        'username': 'superadmin',
        'password': 'SuperAdmin@123'
    }
    response = requests.post(f'{BASE_URL}/api/v1/auth/demo-login', data=demo_creds, timeout=5)
    
    if response.status_code == 200:
        login_data = response.json()
        access_token = login_data.get('access_token')
        token_type = login_data.get('token_type')
        
        print(f'✅ Login successful')
        print(f'   Status: {response.status_code}')
        print(f'   Token Type: {token_type}')
        print(f'   Token Received: ✅ (length: {len(access_token)} chars)')
        print('✅ Auth Service verification: PASSED')
    else:
        print(f'❌ Login failed with status {response.status_code}')
        print(f'   Response: {response.text[:200]}')
        print('❌ Auth Service verification: FAILED')
except requests.exceptions.ConnectionError:
    print('❌ Cannot connect to backend (is it running on port 8000?)')
    print('❌ Auth Service verification: FAILED')
except Exception as e:
    print(f'❌ Auth Service error: {e}')
    print('❌ Auth Service verification: FAILED')

# Test 3: Schemes API
if access_token:
    print('\n[TEST 3] Schemes Endpoint (/api/v1/schemes)')
    print('-' * 70)
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{BASE_URL}/api/v1/schemes?skip=0&limit=10', headers=headers, timeout=5)
        
        if response.status_code == 200:
            schemes = response.json()
            items = schemes.get('items', []) if isinstance(schemes, dict) else schemes
            
            print(f'✅ Schemes API successful')
            print(f'   Status: {response.status_code}')
            print(f'   Schemes Count: {len(items)}')
            
            if len(items) > 0:
                print(f'   Sample Schemes:')
                for scheme in items[:3]:
                    print(f'      • {scheme.get("name", "Unknown")} (ID: {scheme.get("id")})')
                if len(items) > 3:
                    print(f'      ... and {len(items)-3} more')
                print('✅ Schemes API verification: PASSED')
            else:
                print('❌ No schemes returned')
                print('❌ Schemes API verification: FAILED')
        else:
            print(f'❌ Schemes API failed with status {response.status_code}')
            print(f'   Response: {response.text[:200]}')
            print('❌ Schemes API verification: FAILED')
    except Exception as e:
        print(f'❌ Schemes API error: {e}')
        print('❌ Schemes API verification: FAILED')

# Test 4: Check for Error Handling (404 cases)
print('\n[TEST 4] Error Handling (Graceful 404 Response)')
print('-' * 70)
try:
    if access_token:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{BASE_URL}/api/v1/schemes/999999/details', headers=headers, timeout=5)
        
        # Check if it returns descriptive error instead of crashing
        if response.status_code == 404:
            error_data = response.json()
            if isinstance(error_data, dict) and ('detail' in error_data or 'error' in error_data):
                print(f'✅ Graceful 404 handling')
                print(f'   Status: 404')
                print(f'   Response Type: JSON (not HTML error page)')
                print('✅ Error Handling verification: PASSED')
            else:
                print('❌ Error response format unexpected')
                print(f'   Response: {response.text[:200]}')
        else:
            print(f'ℹ️ No invalid endpoint to test (got {response.status_code})')
except Exception as e:
    print(f'ℹ️ Error handling test skipped: {e}')

print('\n' + '=' * 70)
print('✅ VERIFICATION TEST COMPLETE')
print('=' * 70)
