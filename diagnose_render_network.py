"""
Diagnose Render backend network issues
Tests connectivity, CORS, and demo-login endpoint
"""

import requests
import json
from urllib.parse import urljoin

RENDER_URL = "https://fintech-backend-f9vu.onrender.com"
API_URL = f"{RENDER_URL}/api/v1"
FRONTEND_URL = "http://localhost:5172"

print("=" * 80)
print("🔍 NETWORK ERROR DIAGNOSIS - RENDER BACKEND")
print("=" * 80)

# Test 1: Basic connectivity
print("\n1️⃣  TEST: Backend Availability")
print("-" * 80)

try:
    response = requests.get(f"{API_URL}/health", timeout=10)
    print(f"✅ Backend is online (Status: {response.status_code})")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Backend not responding: {str(e)}")
    print("   This could mean:")
    print("   • Render app is still starting (cold start)")
    print("   • Render app crashed")
    print("   • Network connectivity issue")

# Test 2: CORS configuration
print("\n2️⃣  TEST: CORS Headers")
print("-" * 80)

try:
    # Make OPTIONS request to check CORS
    response = requests.options(
        f"{API_URL}/auth/demo-login",
        headers={
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
    }
    
    print("CORS Headers:")
    for header, value in cors_headers.items():
        if value:
            print(f"   ✅ {header}: {value}")
        else:
            print(f"   ❌ {header}: NOT SET")
    
except Exception as e:
    print(f"❌ CORS check failed: {str(e)}")

# Test 3: Demo login direct test
print("\n3️⃣  TEST: Demo Login Endpoint")
print("-" * 80)

try:
    response = requests.post(
        f"{API_URL}/auth/demo-login",
        data={
            "username": "superadmin",
            "password": "SuperAdmin@123"
        },
        timeout=15,
        headers={"Origin": FRONTEND_URL}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"   Access Token: {result.get('access_token', 'N/A')[:30]}...")
        print(f"   Refresh Token: {result.get('refresh_token', 'N/A')[:30]}...")
    else:
        print(f"❌ Failed with status {response.status_code}")
        try:
            print(f"   Response: {response.json()}")
        except:
            print(f"   Response: {response.text[:200]}")
            
except requests.exceptions.Timeout:
    print(f"❌ TIMEOUT: Backend took too long to respond (>15s)")
    print("   Possible causes:")
    print("   • Database connection issue")
    print("   • Render app is cold starting")
    print("   • PostgreSQL not responding")
except requests.exceptions.ConnectionError as e:
    print(f"❌ CONNECTION ERROR: {str(e)}")
    print("   Possible causes:")
    print("   • Backend URL is incorrect")
    print("   • Network connectivity issue")
    print("   • Firewall blocking connection")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# Test 4: POST with Content-Type header (as frontend sends)
print("\n4️⃣  TEST: Demo Login with FormData (Like Frontend)")
print("-" * 80)

try:
    response = requests.post(
        f"{API_URL}/auth/demo-login",
        data={"username": "superadmin", "password": "SuperAdmin@123"},
        timeout=15,
        headers={
            "Origin": FRONTEND_URL,
            "User-Agent": "Mozilla/5.0"
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ FormData POST works!")
    else:
        print(f"❌ Status {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# Test 5: Database connection test
print("\n5️⃣  TEST: Backend Database Connectivity")
print("-" * 80)

try:
    # Call an endpoint that requires database
    response = requests.get(
        f"{API_URL}/auth/me",
        timeout=10,
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    # We expect 401 (invalid token) not 500 (database error)
    if response.status_code == 401:
        print("✅ Database is accessible (got expected 401)")
    elif response.status_code == 500:
        print("❌ Database connection FAILED (500 error)")
        print(f"   Error: {response.json() if response.json() else response.text}")
    else:
        print(f"Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Database test error: {str(e)}")

print("\n" + "=" * 80)
print("📊 DIAGNOSIS SUMMARY")
print("=" * 80)
print("""
If you're seeing a NETWORK ERROR in the browser:

1️⃣  CORS ISSUE (Most Common)
   Fix: Ensure frontend URL is in CORS allowed origins
   Location: backend-api/main.py (CORSMiddleware)
   
2️⃣  COLD START
   Fix: Wait 1-2 minutes for Render to warm up app
   
3️⃣  DATABASE ISSUE
   Fix: Check PostgreSQL connection status in Render
   
4️⃣  TIMEOUT
   Fix: Increase frontend request timeout
   Check Render logs for slow queries
   
5️⃣  RENDER CRASH
   Fix: Check Render logs for errors
   Restart the service

NEXT STEPS:
1. Check if Render backend is responding (test above)
2. Check Render logs for error messages
3. Verify PostgreSQL is connected
4. Check CORS configuration
""")

print("=" * 80 + "\n")
