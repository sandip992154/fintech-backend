import requests
import json

print("=" * 80)
print("🧪 TESTING DEMO-LOGIN ON LOCALHOST:8000")
print("=" * 80)

try:
    response = requests.post(
        "http://localhost:8000/api/v1/auth/demo-login",
        data={"username": "superadmin", "password": "SuperAdmin@123"},
        timeout=30
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS!")
        print(f"   Access Token: {result.get('access_token', 'N/A')[:30]}...")
        print(f"   Refresh Token: {result.get('refresh_token', 'N/A')[:30]}...")
        print(f"   Role: {result.get('role', 'N/A')}")
        print(f"   Token Type: {result.get('token_type', 'N/A')}")
    else:
        print(f"❌ Status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
