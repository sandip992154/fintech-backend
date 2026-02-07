"""
Test script to verify service operator endpoints are working
"""
import requests


def test_operators_endpoint():
    """Test the service operators endpoint"""
    
    try:
        # Test without auth to see if endpoint exists
        url = "http://localhost:8000/api/v1/operators"
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        elif response.status_code == 200:
            print("✅ Endpoint working without auth")
            data = response.json()
            print(f"Number of operators: {len(data)}")
        elif response.status_code == 500:
            print("❌ Server error - check imports and model issues")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_operators_endpoint()