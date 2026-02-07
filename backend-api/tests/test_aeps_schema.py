#!/usr/bin/env python3
"""
Direct schema validation test for AEPS commission without HTTP requests
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.schemas.scheme_schemas import CommissionCreate
from pydantic import ValidationError

def test_aeps_schema_validation():
    """Test AEPS commission schema validation directly"""
    
    print("AEPS Commission Schema Validation Test")
    print("="*50)
    
    # Test 1: AEPS commission without slabs
    print("\n1. Testing AEPS commission WITHOUT slabs:")
    aeps_data_no_slabs = {
        "service_type": "aeps",
        "operator_id": 1,  # Must be integer
        "commission_type": "percentage",  # Must be exact enum value
        # Add role-based commission values (from RoleCommissionValues)
        "superadmin_commission": 5.0,
        "admin_commission": 4.0,
        "whitelabel_commission": 3.0,
        "masterdistributor_commission": 2.5,
        "distributor_commission": 2.0,
        "retailer_commission": 1.5,
        "customer_commission": 1.0
        # No slabs field - should be allowed now
    }
    
    try:
        commission = CommissionCreate(**aeps_data_no_slabs)
        print("✅ SUCCESS: AEPS commission created without slabs!")
        print(f"   Commission data: {commission.model_dump()}")
        test1_passed = True
    except ValidationError as e:
        print("❌ VALIDATION ERROR:")
        for error in e.errors():
            print(f"   {error['loc']}: {error['msg']}")
        test1_passed = False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        test1_passed = False
    
    # Test 2: AEPS commission with empty slabs list  
    print("\n2. Testing AEPS commission WITH empty slabs list:")
    aeps_data_empty_slabs = {
        "service_type": "aeps",
        "operator_id": 2,
        "commission_type": "percentage",
        "superadmin_commission": 5.0,
        "admin_commission": 4.0,
        "whitelabel_commission": 3.0,
        "masterdistributor_commission": 2.5,
        "distributor_commission": 2.0,
        "retailer_commission": 1.5,
        "customer_commission": 1.0,
        "slabs": []  # Empty slabs - should be allowed now
    }
    
    try:
        commission = CommissionCreate(**aeps_data_empty_slabs)
        print("✅ SUCCESS: AEPS commission created with empty slabs!")
        print(f"   Commission data: {commission.model_dump()}")
        test2_passed = True
    except ValidationError as e:
        print("❌ VALIDATION ERROR:")
        for error in e.errors():
            print(f"   {error['loc']}: {error['msg']}")
        test2_passed = False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        test2_passed = False
    
    # Test 3: AEPS commission with valid slabs
    print("\n3. Testing AEPS commission WITH valid slabs:")
    aeps_data_with_slabs = {
        "service_type": "aeps",
        "operator_id": 3,
        "commission_type": "percentage",
        "superadmin_commission": 5.0,
        "admin_commission": 4.0,
        "whitelabel_commission": 3.0,
        "masterdistributor_commission": 2.5,
        "distributor_commission": 2.0,
        "retailer_commission": 1.5,
        "customer_commission": 1.0,
        "slabs": [
            {
                "slab_min": 100.0,  # Correct field names
                "slab_max": 500.0,
                "superadmin_commission": 1.0,
                "admin_commission": 0.9,
                "whitelabel_commission": 0.8,
                "masterdistributor_commission": 0.7,
                "distributor_commission": 0.6,
                "retailer_commission": 0.5,
                "customer_commission": 0.4
            },
            {
                "slab_min": 501.0,
                "slab_max": 1000.0,
                "superadmin_commission": 1.5,
                "admin_commission": 1.4,
                "whitelabel_commission": 1.3,
                "masterdistributor_commission": 1.2,
                "distributor_commission": 1.1,
                "retailer_commission": 1.0,
                "customer_commission": 0.9
            }
        ]
    }
    
    try:
        commission = CommissionCreate(**aeps_data_with_slabs)
        print("✅ SUCCESS: AEPS commission created with valid slabs!")
        print(f"   Commission data: {commission.model_dump()}")
        test3_passed = True
    except ValidationError as e:
        print("❌ VALIDATION ERROR:")
        for error in e.errors():
            print(f"   {error['loc']}: {error['msg']}")
        test3_passed = False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        test3_passed = False
    
    # Test 4: Non-AEPS commission with slabs (for comparison)
    print("\n4. Testing non-AEPS commission with slabs:")
    non_aeps_data = {
        "service_type": "mobile_recharge",  # Correct enum value
        "operator_id": 4,
        "commission_type": "percentage",
        "superadmin_commission": 5.0,
        "admin_commission": 4.0,
        "whitelabel_commission": 3.0,
        "masterdistributor_commission": 2.5,
        "distributor_commission": 2.0,
        "retailer_commission": 1.5,
        "customer_commission": 1.0,
        "slabs": [
            {
                "slab_min": 10.0,
                "slab_max": 100.0,
                "superadmin_commission": 2.0,
                "admin_commission": 1.9,
                "whitelabel_commission": 1.8,
                "masterdistributor_commission": 1.7,
                "distributor_commission": 1.6,
                "retailer_commission": 1.5,
                "customer_commission": 1.4
            }
        ]
    }
    
    try:
        commission = CommissionCreate(**non_aeps_data)
        print("✅ SUCCESS: Non-AEPS commission created with slabs!")
        test4_passed = True
    except ValidationError as e:
        print("❌ VALIDATION ERROR:")
        for error in e.errors():
            print(f"   {error['loc']}: {error['msg']}")
        test4_passed = False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        test4_passed = False
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"AEPS without slabs field: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"AEPS with empty slabs: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"AEPS with valid slabs: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    print(f"Non-AEPS with slabs: {'✅ PASS' if test4_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 AEPS validation fix successful!")
        print("AEPS commissions can now be created without requiring slabs.")
    else:
        print("\n⚠️  AEPS validation fix needs more work.")
        
    return test1_passed and test2_passed

if __name__ == "__main__":
    test_aeps_schema_validation()