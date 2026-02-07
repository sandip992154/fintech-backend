"""
Test script to debug the SuperAdmin authentication issue
"""
import requests
import json


def test_login_and_scheme_creation():
    """Test login and scheme creation to debug the role issue"""
    base_url = "http://localhost:8000"
    
    try:
        # Login as superadmin
        login_data = {
            "username": "superadmin",
            "password": "SuperAdmin@123"
        }
        
        login_response = requests.post(
            f"{base_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"✅ Login successful. Token: {token[:50]}...")
            
            # Test scheme creation
            scheme_data = {
                "name": "Test Scheme Debug",
                "description": "Testing debug for permissions"
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            create_response = requests.post(
                f"{base_url}/api/v1/schemes/",
                json=scheme_data,
                headers=headers
            )
            
            print(f"Create Scheme Status: {create_response.status_code}")
            print(f"Create Scheme Response: {create_response.text}")
            
            if create_response.status_code == 403:
                print("❌ Still getting 403 error - check server logs for debug output")
            elif create_response.status_code == 201:
                print("✅ Scheme creation successful!")
            
        else:
            print(f"❌ Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_login_and_scheme_creation()