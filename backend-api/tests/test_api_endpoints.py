#!/usr/bin/env python3
"""
Test scheme management API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test various scheme management endpoints"""
    
    print("🧪 Testing Scheme Management API Endpoints")
    print("=" * 50)
    
    # Test 1: Get all schemes
    print("\n1. Testing GET /api/schemes")
    try:
        response = requests.get(f"{BASE_URL}/api/schemes")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            schemes = response.json()
            print(f"   Found {len(schemes)} schemes")
            for scheme in schemes[:2]:  # Show first 2
                print(f"   - {scheme['name']}: {scheme['description']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection error: {str(e)}")
    
    # Test 2: Get all service operators
    print("\n2. Testing GET /api/service-operators")
    try:
        response = requests.get(f"{BASE_URL}/api/service-operators")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            operators = response.json()
            print(f"   Found {len(operators)} operators")
            for operator in operators[:3]:  # Show first 3
                print(f"   - {operator['name']} ({operator['service_type']})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection error: {str(e)}")
    
    # Test 3: Get all commissions
    print("\n3. Testing GET /api/commissions")
    try:
        response = requests.get(f"{BASE_URL}/api/commissions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            commissions = response.json()
            print(f"   Found {len(commissions)} commissions")
            for commission in commissions[:2]:  # Show first 2
                print(f"   - Type: {commission['commission_type']}, Service: {commission['service_type']}")
                print(f"     Retailer: {commission['retailer']}, Distributor: {commission['distributor']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection error: {str(e)}")
    
    # Test 4: Get commission slabs
    print("\n4. Testing GET /api/commission-slabs")
    try:
        response = requests.get(f"{BASE_URL}/api/commission-slabs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            slabs = response.json()
            print(f"   Found {len(slabs)} commission slabs")
            for slab in slabs[:2]:  # Show first 2
                print(f"   - Range: ₹{slab['slab_min']:.0f} - ₹{slab['slab_max']:.0f}")
                print(f"     Retailer: ₹{slab['retailer']:.0f}, Distributor: ₹{slab['distributor']:.0f}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection error: {str(e)}")
    
    # Test 5: API Documentation
    print("\n5. Testing API Documentation")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"   API Docs Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ API documentation is accessible")
            print(f"   📖 Visit: {BASE_URL}/docs")
        else:
            print(f"   Error accessing docs: {response.text}")
    except Exception as e:
        print(f"   Connection error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Testing completed!")
    print(f"\n🌐 Access the API documentation at: {BASE_URL}/docs")
    print(f"🔧 Test the endpoints interactively at: {BASE_URL}/redoc")

if __name__ == "__main__":
    test_endpoints()