"""
Test script for scheme endpoints
"""
import requests
import json


def test_scheme_endpoint():
    """Test the scheme list endpoint"""
    try:
        # Test without authentication first to see if we get a 401 or 500
        url = "http://localhost:8000/api/v1/schemes/"
        response = requests.get(url)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("✅ Good! Getting 401 Unauthorized instead of 500 serialization error")
            print("This means the serialization fix worked")
        elif response.status_code == 500:
            print("❌ Still getting 500 error")
            print(f"Response content: {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    test_scheme_endpoint()