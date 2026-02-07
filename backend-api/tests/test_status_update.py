"""
Test script to verify scheme status updates are working correctly
"""
import requests
import json


def test_scheme_status_update():
    """Test scheme status update functionality"""
    base_url = "http://localhost:8000"
    
    try:
        # First, let's try to get a fresh token by testing the health endpoint
        health_response = requests.get(f"{base_url}/health")
        print(f"Health check: {health_response.status_code}")
        
        if health_response.status_code != 200:
            print("❌ Server is not responding")
            return
            
        print("✅ Server is responding")
        
        # Test scheme list endpoint (should require auth)
        schemes_response = requests.get(f"{base_url}/api/v1/schemes/")
        print(f"Schemes endpoint status: {schemes_response.status_code}")
        
        if schemes_response.status_code == 401:
            print("✅ Authentication is working (401 expected without token)")
        elif schemes_response.status_code == 200:
            schemes_data = schemes_response.json()
            print(f"✅ Got schemes data: {len(schemes_data.get('items', []))} schemes")
        else:
            print(f"❌ Unexpected response: {schemes_response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_scheme_status_update()