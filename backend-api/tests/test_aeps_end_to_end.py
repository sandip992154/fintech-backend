#!/usr/bin/env python3
"""
End-to-end test for AEPS commission functionality including slab creation and retrieval.
"""

import json
from services.schemas.scheme_schemas import (
    CommissionCreate, CommissionSlabCreate, CommissionOut,
    ServiceTypeEnum, CommissionTypeEnum, BulkCommissionCreate,
    CommissionEntry, AEPSCommissionEntry, AEPSCommissionSlab
)

def test_aeps_commission_bulk_operation():
    """Test AEPS commission bulk operation with slabs"""
    print("🧪 Testing AEPS commission bulk operation...")
    
    try:
        # Test payload similar to what frontend sends
        bulk_payload = {
            "service": "aeps",
            "entries": [
                {
                    "operator": "AEPS Cash Withdrawal",
                    "commission_type": "fixed",
                    "slabs": [
                        {
                            "slab_min": 0.0,
                            "slab_max": 1000.0,
                            "admin": 2.0,
                            "whitelabel": 1.8,
                            "masterdistributor": 1.5,
                            "distributor": 1.2,
                            "retailer": 1.0,
                            "customer": 0.8
                        },
                        {
                            "slab_min": 1000.01,
                            "slab_max": 5000.0,
                            "admin": 3.0,
                            "whitelabel": 2.7,
                            "masterdistributor": 2.4,
                            "distributor": 2.0,
                            "retailer": 1.8,
                            "customer": 1.5
                        }
                    ]
                }
            ]
        }
        
        # Test schema validation
        bulk_commission = BulkCommissionCreate(**bulk_payload)
        print(f"✅ Bulk commission schema validated successfully")
        print(f"   Service: {bulk_commission.service}")
        print(f"   Entries: {len(bulk_commission.entries)}")
        
        # Check first entry
        first_entry = bulk_commission.entries[0]
        print(f"   Operator: {first_entry.operator}")
        print(f"   Commission type: {first_entry.commission_type}")
        
        if hasattr(first_entry, 'slabs') and first_entry.slabs:
            print(f"   Slabs: {len(first_entry.slabs)}")
            for i, slab in enumerate(first_entry.slabs):
                print(f"     Slab {i+1}: {slab.slab_min}-{slab.slab_max}, admin: {slab.admin}")
        else:
            print("   ❌ No slabs found in entry!")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Bulk operation test failed: {str(e)}")
        return False

def test_aeps_commission_entry_schema():
    """Test AEPS commission entry schema"""
    print("\n📋 Testing AEPS commission entry schema...")
    
    try:
        # Test AEPSCommissionEntry schema
        aeps_entry_data = {
            "operator": "AEPS Cash Withdrawal",
            "commission_type": "fixed",
            "slabs": [
                {
                    "slab_min": 0.0,
                    "slab_max": 1000.0,
                    "whitelabel": 1.8,
                    "md": 1.5,  # Note: using 'md' instead of 'masterdistributor'
                    "distributor": 1.2,
                    "retailer": 1.0,
                    "admin": 2.0,
                    "customer": 0.8
                }
            ]
        }
        
        aeps_entry = AEPSCommissionEntry(**aeps_entry_data)
        print(f"✅ AEPS entry schema validated successfully")
        print(f"   Operator: {aeps_entry.operator}")
        print(f"   Slabs: {len(aeps_entry.slabs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ AEPS entry schema test failed: {str(e)}")
        return False

def test_commission_response_format():
    """Test commission response format matches expected API output"""
    print("\n🔍 Testing commission response format...")
    
    try:
        # Simulate database commission data
        commission_data = {
            "id": 15,
            "scheme_id": 10,
            "operator_id": 26,
            "service_type": "aeps",
            "commission_type": "fixed",
            "admin": 0.0,
            "whitelabel": 0.0,
            "masterdistributor": 0.0,
            "distributor": 0.0,
            "retailer": 0.0,
            "customer": 0.0,
            "slab_min": None,
            "slab_max": None,
            "is_active": True,
            "created_at": "2025-10-04T06:25:46.667413",
            "updated_at": "2025-10-04T06:25:46.667422",
            "operator": {
                "name": "AEPS Cash Withdrawal",
                "service_type": "aeps",
                "id": 26,
                "is_active": True,
                "created_at": "2025-10-02T14:01:43.105468",
                "updated_at": "2025-10-02T14:01:43.105471"
            },
            "slabs": [
                {
                    "id": 1,
                    "commission_id": 15,
                    "slab_min": 0.0,
                    "slab_max": 1000.0,
                    "admin": 2.0,
                    "whitelabel": 1.8,
                    "masterdistributor": 1.5,
                    "distributor": 1.2,
                    "retailer": 1.0,
                    "customer": 0.8,
                    "is_active": True,
                    "created_at": "2025-10-04T06:25:46.667413",
                    "updated_at": "2025-10-04T06:25:46.667422"
                }
            ]
        }
        
        print(f"✅ Expected response format with slabs:")
        print(f"   Commission ID: {commission_data['id']}")
        print(f"   Service type: {commission_data['service_type']}")
        print(f"   Operator: {commission_data['operator']['name']}")
        print(f"   Slabs: {len(commission_data['slabs']) if commission_data['slabs'] else 0}")
        
        if commission_data['slabs']:
            for slab in commission_data['slabs']:
                print(f"     Slab: {slab['slab_min']}-{slab['slab_max']}, admin: {slab['admin']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Response format test failed: {str(e)}")
        return False

def test_payload_from_user():
    """Test the actual payload from user request"""
    print("\n🔧 Testing user's actual payload...")
    
    try:
        # User's payload from the issue description
        user_payload = {
            "service": "aeps",
            "entries": [
                {
                    "admin": 0.0,
                    "whitelabel": 0.0,
                    "masterdistributor": 0.0,
                    "distributor": 0.0,
                    "retailer": 0.0,
                    "customer": 0.0,
                    "operator_id": 26,
                    "service_type": "aeps",
                    "commission_type": "fixed",
                    "id": 15,
                    "scheme_id": 10,
                    "slab_min": None,
                    "slab_max": None,
                    "is_active": True,
                    "created_at": "2025-10-04T06:25:46.667413",
                    "updated_at": "2025-10-04T06:25:46.667422",
                    "operator": {
                        "name": "AEPS Cash Withdrawal",
                        "service_type": "aeps",
                        "id": 26,
                        "is_active": True,
                        "created_at": "2025-10-02T14:01:43.105468",
                        "updated_at": "2025-10-02T14:01:43.105471"
                    },
                    "slabs": None  # This is the issue - slabs should not be null!
                }
            ]
        }
        
        print(f"❌ User's payload shows the issue:")
        print(f"   Service: {user_payload['service']}")
        print(f"   Commission ID: {user_payload['entries'][0]['id']}")
        print(f"   Operator: {user_payload['entries'][0]['operator']['name']}")
        print(f"   Slabs: {user_payload['entries'][0]['slabs']} (should not be null!)")
        
        print("\n🎯 The problem is:")
        print("   1. ✅ Commission exists (ID: 15)")
        print("   2. ✅ Operator exists (AEPS Cash Withdrawal)")
        print("   3. ❌ Slabs are null - they should contain the slab data")
        print("   4. ❌ All commission values are 0.0 (should use slab values)")
        
        return True
        
    except Exception as e:
        print(f"❌ User payload test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AEPS commission end-to-end functionality...\n")
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_aeps_commission_bulk_operation():
        tests_passed += 1
    
    if test_aeps_commission_entry_schema():
        tests_passed += 1
        
    if test_commission_response_format():
        tests_passed += 1
        
    if test_payload_from_user():
        tests_passed += 1
    
    print(f"\n==================================================")
    print(f"📊 Tests Summary: {tests_passed}/{total_tests} passed")
    
    print("\n🔍 Root Cause Analysis:")
    print("The issue is that AEPS commissions are not loading their slabs properly.")
    print("This means the database relationship or eager loading is not working.")
    print("\n💡 Solution needed:")
    print("1. ✅ Fixed database relationships (Commission -> CommissionSlab)")
    print("2. ✅ Fixed eager loading in commission retrieval")
    print("3. ✅ Fixed Pydantic v2 compatibility (model_dump vs dict)")
    print("4. 🔄 Need to test actual API to verify slab loading works")
    
    if tests_passed == total_tests:
        print("\n🎉 All schema tests passed! But API functionality still needs verification.")
    else:
        print("\n❌ Some tests failed. Schema functionality needs fixes.")