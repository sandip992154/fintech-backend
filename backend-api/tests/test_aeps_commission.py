#!/usr/bin/env python3
"""
Test script to verify AEPS commission creation without slabs
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
SCHEME_ID = "test_scheme_1"  # We'll use a test scheme ID
COMMISSION_ENDPOINT = f"{BASE_URL}/api/v1/schemes/{SCHEME_ID}/commissions"

def test_aeps_commission_creation():
    """Test creating AEPS commission without slabs"""
    
    # Sample AEPS commission data without slabs
    commission_data = {
        "service_type": "aeps",
        "operator_id": "test_operator_1",
        "circle_id": "test_circle_1", 
        "commission_type": "percentage",
        "commission_value": 2.5,
        "gst_applicable": True,
        "tds_applicable": True,
        "status": "active"
        # Note: No 'slabs' field included - this should work now
    }
    
    print("Testing AEPS commission creation without slabs...")
    print(f"Data: {json.dumps(commission_data, indent=2)}")
    
    try:
        response = requests.post(
            COMMISSION_ENDPOINT,
            json=commission_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: AEPS commission created without slabs!")
            return True
        elif response.status_code == 422:
            print("❌ VALIDATION ERROR: Still requiring slabs for AEPS")
            return False
        else:
            print(f"❌ UNEXPECTED ERROR: Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend server not running on port 8000")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        return False

def test_aeps_commission_with_slabs():
    """Test creating AEPS commission with slabs for comparison"""
    
    commission_data = {
        "service_type": "aeps",
        "operator_id": "test_operator_2",
        "circle_id": "test_circle_2",
        "commission_type": "slab",
        "commission_value": 0,
        "gst_applicable": True,
        "tds_applicable": True,
        "status": "active",
        "slabs": [
            {
                "min_amount": 100,
                "max_amount": 500,
                "commission_type": "percentage",
                "commission_value": 1.0
            },
            {
                "min_amount": 501,
                "max_amount": 1000,
                "commission_type": "percentage", 
                "commission_value": 1.5
            }
        ]
    }
    
    print("\n" + "="*50)
    print("Testing AEPS commission creation WITH slabs...")
    print(f"Data: {json.dumps(commission_data, indent=2)}")
    
    try:
        response = requests.post(
            COMMISSION_ENDPOINT,
            json=commission_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: AEPS commission created with slabs!")
            return True
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("AEPS Commission Validation Test")
    print("="*50)
    
    # Test without slabs (should work now)
    test1_result = test_aeps_commission_creation()
    
    # Test with slabs (should always work)
    test2_result = test_aeps_commission_with_slabs()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"AEPS without slabs: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"AEPS with slabs: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result:
        print("\n🎉 AEPS validation fix successful!")
        print("AEPS commissions can now be created without slabs.")
        print("Slabs can be managed separately via the AEPS Slab Manager.")
    else:
        print("\n⚠️  AEPS validation fix needs more work.")