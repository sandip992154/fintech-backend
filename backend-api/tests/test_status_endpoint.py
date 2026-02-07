"""
Quick test for scheme status update endpoint
"""
import requests
import json


def test_status_endpoint():
    """Test the scheme status update endpoint directly"""
    
    # First test without auth to see the response structure
    url = "http://localhost:8000/api/v1/schemes/5/status"
    data = {"is_active": False}
    
    try:
        response = requests.patch(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        elif response.status_code == 422:
            print("✅ Endpoint exists but has validation error")
            print("Response details:", response.json())
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_status_endpoint()