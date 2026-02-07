#!/usr/bin/env python3
"""
Test commission role hierarchy permissions
"""

from services.utils.role_hierarchy import RoleHierarchy

def test_commission_role_permissions():
    """Test that users can only set commissions for subordinate roles"""
    print("🧪 Testing Commission Role Hierarchy Permissions")
    print("=" * 60)
    
    # Test 1: Superadmin should be able to set all roles
    print("\n📝 Test 1: Superadmin setting commissions for all roles")
    commission_data_1 = {
        "superadmin": 5.0,
        "admin": 4.0,
        "whitelabel": 3.0,
        "masterdistributor": 2.0,
        "distributor": 1.5,
        "retailer": 1.0,
        "customer": 0.5
    }
    errors_1 = RoleHierarchy.validate_commission_role_permissions("superadmin", commission_data_1)
    print(f"   Errors: {errors_1}")
    print(f"   Result: {'✅ PASS' if not errors_1 else '❌ FAIL'}")
    
    # Test 2: Admin should NOT be able to set superadmin commission
    print("\n📝 Test 2: Admin trying to set superadmin commission")
    commission_data_2 = {
        "superadmin": 5.0,  # This should fail
        "admin": 4.0,
        "whitelabel": 3.0,
        "distributor": 1.5
    }
    errors_2 = RoleHierarchy.validate_commission_role_permissions("admin", commission_data_2)
    print(f"   Errors: {errors_2}")
    print(f"   Result: {'✅ PASS' if 'superadmin' in errors_2 else '❌ FAIL'} (should have superadmin error)")
    
    # Test 3: Admin should be able to set subordinate roles
    print("\n📝 Test 3: Admin setting commissions for subordinate roles only")
    commission_data_3 = {
        "admin": 4.0,
        "whitelabel": 3.0,
        "masterdistributor": 2.0,
        "distributor": 1.5,
        "retailer": 1.0,
        "customer": 0.5
    }
    errors_3 = RoleHierarchy.validate_commission_role_permissions("admin", commission_data_3)
    print(f"   Errors: {errors_3}")
    print(f"   Result: {'✅ PASS' if not errors_3 else '❌ FAIL'}")
    
    # Test 4: Whitelabel should NOT be able to set admin commission
    print("\n📝 Test 4: Whitelabel trying to set admin commission")
    commission_data_4 = {
        "admin": 4.0,  # This should fail
        "whitelabel": 3.0,
        "distributor": 1.5
    }
    errors_4 = RoleHierarchy.validate_commission_role_permissions("whitelabel", commission_data_4)
    print(f"   Errors: {errors_4}")
    print(f"   Result: {'✅ PASS' if 'admin' in errors_4 else '❌ FAIL'} (should have admin error)")
    
    # Test 5: Distributor should NOT be able to set any higher role commissions
    print("\n📝 Test 5: Distributor trying to set higher role commissions")
    commission_data_5 = {
        "whitelabel": 3.0,  # This should fail
        "distributor": 1.5,
        "retailer": 1.0
    }
    errors_5 = RoleHierarchy.validate_commission_role_permissions("distributor", commission_data_5)
    print(f"   Errors: {errors_5}")
    print(f"   Result: {'✅ PASS' if 'whitelabel' in errors_5 else '❌ FAIL'} (should have whitelabel error)")
    
    # Summary
    print(f"\n📋 Summary:")
    all_tests_pass = (
        not errors_1 and  # Superadmin should have no errors
        'superadmin' in errors_2 and  # Admin should get superadmin error
        not errors_3 and  # Admin should have no errors for subordinates
        'admin' in errors_4 and  # Whitelabel should get admin error
        'whitelabel' in errors_5  # Distributor should get whitelabel error
    )
    print(f"   All tests: {'✅ PASS' if all_tests_pass else '❌ SOME FAILED'}")
    
    return all_tests_pass

if __name__ == "__main__":
    test_commission_role_permissions()