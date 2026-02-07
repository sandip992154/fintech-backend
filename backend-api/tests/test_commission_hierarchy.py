#!/usr/bin/env python3
"""
Test commission hierarchy validation logic
"""

from services.utils.role_hierarchy import RoleHierarchy

def test_commission_hierarchy():
    """Test the commission hierarchy validation"""
    print("🧪 Testing Commission Hierarchy Validation")
    print("=" * 50)
    
    # Test case 1: Your actual data that was failing
    test_data_1 = {
        "admin": 1,
        "whitelabel": 0.8,
        "masterdistributor": 0.7,
        "distributor": 0.4,
        "retailer": 0.3,
        "customer": 0.1
    }
    
    print("\n📝 Test 1: Valid hierarchy (missing superadmin)")
    print(f"   Data: {test_data_1}")
    result_1 = RoleHierarchy.validate_commission_hierarchy(test_data_1)
    print(f"   Result: {'✅ PASS' if result_1 else '❌ FAIL'}")
    
    # Test case 2: Invalid hierarchy
    test_data_2 = {
        "admin": 1,
        "whitelabel": 2,  # This should fail - higher than admin
        "distributor": 0.5,
        "retailer": 0.3
    }
    
    print("\n📝 Test 2: Invalid hierarchy (whitelabel > admin)")
    print(f"   Data: {test_data_2}")
    result_2 = RoleHierarchy.validate_commission_hierarchy(test_data_2)
    print(f"   Result: {'✅ PASS' if not result_2 else '❌ FAIL'} (should fail)")
    
    # Test case 3: Valid hierarchy with all roles
    test_data_3 = {
        "superadmin": 5,
        "admin": 4,
        "whitelabel": 3,
        "masterdistributor": 2,
        "distributor": 1.5,
        "retailer": 1,
        "customer": 0.5
    }
    
    print("\n📝 Test 3: Valid hierarchy (all roles present)")
    print(f"   Data: {test_data_3}")
    result_3 = RoleHierarchy.validate_commission_hierarchy(test_data_3)
    print(f"   Result: {'✅ PASS' if result_3 else '❌ FAIL'}")
    
    # Test case 4: Only some roles present
    test_data_4 = {
        "distributor": 2,
        "retailer": 1,
        "customer": 0.5
    }
    
    print("\n📝 Test 4: Valid hierarchy (only lower roles)")
    print(f"   Data: {test_data_4}")
    result_4 = RoleHierarchy.validate_commission_hierarchy(test_data_4)
    print(f"   Result: {'✅ PASS' if result_4 else '❌ FAIL'}")
    
    # Summary
    print("\n📋 Summary:")
    all_passed = result_1 and not result_2 and result_3 and result_4
    print(f"   All tests: {'✅ PASS' if all_passed else '❌ SOME FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_commission_hierarchy()