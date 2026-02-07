#!/usr/bin/env python3
"""
Test script to verify AEPS slab endpoints functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_slab_endpoints():
    """Test AEPS slab management endpoints"""
    
    print("AEPS Slab Endpoints Test")
    print("="*50)
    
    # Test 1: Create a test commission first (needed for slab operations)
    print("\n1. Creating test AEPS commission...")
    commission_data = {
        "service_type": "aeps",
        "operator_id": 1,
        "commission_type": "percentage",
        "superadmin_commission": 5.0,
        "admin_commission": 4.0,
        "whitelabel_commission": 3.0,
        "masterdistributor_commission": 2.5,
        "distributor_commission": 2.0,
        "retailer_commission": 1.5,
        "customer_commission": 1.0
    }
    
    try:
        # Note: Using scheme_id = 1 (assuming it exists)
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/schemes/1/commissions",
            json=commission_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Commission creation status: {response.status_code}")
        if response.status_code == 201:
            commission = response.json()
            commission_id = commission.get('id')
            print(f"✅ Commission created with ID: {commission_id}")
        else:
            print(f"❌ Commission creation failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend server not running")
        return False
    
    if not commission_id:
        print("❌ Could not get commission ID")
        return False
    
    # Test 2: Get slabs for the commission (should be empty initially)
    print(f"\n2. Getting slabs for commission {commission_id}...")
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/commissions/{commission_id}/slabs",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Get slabs status: {response.status_code}")
        if response.status_code == 200:
            slabs = response.json()
            print(f"✅ Got slabs: {len(slabs)} items")
            print(f"   Slabs: {slabs}")
        else:
            print(f"❌ Get slabs failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Get slabs error: {str(e)}")
    
    # Test 3: Create a new slab
    print(f"\n3. Creating new slab for commission {commission_id}...")
    slab_data = {
        "commission_id": commission_id,
        "slab_min": 100.0,
        "slab_max": 500.0,
        "superadmin": 1.5,
        "admin": 1.4,
        "whitelabel": 1.3,
        "masterdistributor": 1.2,
        "distributor": 1.1,
        "retailer": 1.0,
        "customer": 0.9
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/commission-slabs",
            json=slab_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Create slab status: {response.status_code}")
        if response.status_code == 201:
            slab = response.json()
            slab_id = slab.get('id')
            print(f"✅ Slab created with ID: {slab_id}")
            print(f"   Slab details: {json.dumps(slab, indent=2)}")
        else:
            print(f"❌ Create slab failed: {response.text}")
            slab_id = None
            
    except Exception as e:
        print(f"❌ Create slab error: {str(e)}")
        slab_id = None
    
    # Test 4: Update the slab (if created successfully)
    if slab_id:
        print(f"\n4. Updating slab {slab_id}...")
        update_data = {
            "slab_min": 100.0,
            "slab_max": 500.0,
            "superadmin": 2.0,  # Updated value
            "admin": 1.9,
            "whitelabel": 1.8,
            "masterdistributor": 1.7,
            "distributor": 1.6,
            "retailer": 1.5,
            "customer": 1.4
        }
        
        try:
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/commission-slabs/{slab_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Update slab status: {response.status_code}")
            if response.status_code == 200:
                updated_slab = response.json()
                print(f"✅ Slab updated successfully")
                print(f"   Updated superadmin commission: {updated_slab.get('superadmin')}")
            else:
                print(f"❌ Update slab failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Update slab error: {str(e)}")
    
    # Test 5: Get slabs again to verify
    print(f"\n5. Getting slabs again to verify...")
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/commissions/{commission_id}/slabs",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Get slabs status: {response.status_code}")
        if response.status_code == 200:
            slabs = response.json()
            print(f"✅ Got slabs: {len(slabs)} items")
            if slabs:
                print(f"   First slab superadmin commission: {slabs[0].get('superadmin')}")
        else:
            print(f"❌ Get slabs failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Get slabs error: {str(e)}")
    
    # Test 6: Delete the slab (if created successfully)
    if slab_id:
        print(f"\n6. Deleting slab {slab_id}...")
        try:
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/commission-slabs/{slab_id}",
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Delete slab status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Slab deleted: {result.get('message')}")
            else:
                print(f"❌ Delete slab failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Delete slab error: {str(e)}")
    
    print("\n" + "="*50)
    print("AEPS Slab Endpoints Test Complete!")
    
    return True

if __name__ == "__main__":
    test_slab_endpoints()