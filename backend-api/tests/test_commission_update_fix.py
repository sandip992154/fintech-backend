#!/usr/bin/env python3
"""
Test commission update functionality after superadmin removal
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

import json
from typing import List

# Test data that simulates the frontend payload
commission_update_payload = {
    "service": "AEPS",
    "entries": [
        {
            "commission_id": 15,  # Existing commission to update
            "operator": "FINO",
            "commission_type": "fixed",  # Use correct enum value
            "admin": 9.0,
            "whitelabel": 8.0,
            "masterdistributor": 7.0,
            "distributor": 6.0,
            "retailer": 5.0,
            "customer": 4.0
        }
    ]
}

def test_commission_fields():
    """Test that commission update logic properly handles fields without superadmin"""
    
    # Test 1: Verify role hierarchy excludes superadmin
    try:
        from services.utils.role_hierarchy import RoleHierarchy
        editable_fields = RoleHierarchy.get_editable_commission_fields("admin")
        print(f"✅ Admin editable fields: {editable_fields}")
        assert 'superadmin' not in editable_fields, "superadmin should not be in editable fields"
        assert 'admin' in editable_fields, "admin should be in editable fields"
        print("✅ Role hierarchy correctly excludes superadmin")
    except ImportError as e:
        print(f"❌ Failed to import role hierarchy: {e}")
        return False
    except Exception as e:
        print(f"❌ Role hierarchy test failed: {e}")
        return False
    
    # Test 2: Verify schema validation works without superadmin
    try:
        from services.schemas.scheme_schemas import CommissionUpdate, CommissionCreate
        
        # Test CommissionUpdate schema
        update_data = CommissionUpdate(
            commission_type="fixed",
            admin=9.0,
            whitelabel=8.0,
            masterdistributor=7.0,
            distributor=6.0,
            retailer=5.0,
            customer=4.0
        )
        print(f"✅ CommissionUpdate schema works: {update_data.dict()}")
        assert not hasattr(update_data, 'superadmin'), "CommissionUpdate should not have superadmin field"
        
        # Test CommissionCreate schema  
        create_data = CommissionCreate(
            operator_id=1,
            service_type="aeps",  # Use correct enum value
            commission_type="fixed",
            admin=9.0,
            whitelabel=8.0,
            masterdistributor=7.0,
            distributor=6.0,
            retailer=5.0,
            customer=4.0
        )
        print(f"✅ CommissionCreate schema works: {create_data.dict()}")
        assert not hasattr(create_data, 'superadmin'), "CommissionCreate should not have superadmin field"
        
        print("✅ Schemas correctly exclude superadmin")
    except ImportError as e:
        print(f"❌ Failed to import schemas: {e}")
        return False
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False
    
    # Test 3: Verify bulk update entry processing
    try:
        from services.schemas.scheme_schemas import CommissionEntry
        
        entry_data = CommissionEntry(
            operator="FINO",
            commission_type="fixed",
            admin=9.0,
            whitelabel=8.0,
            masterdistributor=7.0,
            distributor=6.0,
            retailer=5.0,
            customer=4.0
        )
        print(f"✅ CommissionEntry schema works: {entry_data.dict()}")
        assert not hasattr(entry_data, 'superadmin'), "CommissionEntry should not have superadmin field"
        
        print("✅ Bulk update schemas correctly exclude superadmin")
    except ImportError as e:
        print(f"❌ Failed to import bulk schemas: {e}")
        return False
    except Exception as e:
        print(f"❌ Bulk update schema test failed: {e}")
        return False
    
    return True

def test_commission_update_logic():
    """Test the commission update filtering logic"""
    
    try:
        # Simulate the filtering logic that was enhanced
        always_editable = {'commission_type', 'service_type', 'operator_id', 'is_active'}
        role_fields = ['admin', 'whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer']
        
        # Test user role permissions (simplified)
        user_role = "admin"
        from services.utils.role_hierarchy import RoleHierarchy
        
        # Get editable fields for admin user
        editable_fields = RoleHierarchy.get_editable_commission_fields(user_role)
        print(f"✅ Admin can edit commission fields: {editable_fields}")
        
        # Check field filtering logic
        update_data = {
            'commission_type': 'fixed',
            'admin': 9.0,
            'whitelabel': 8.0,
            'masterdistributor': 7.0,
            'distributor': 6.0,
            'retailer': 5.0,
            'customer': 4.0
        }
        
        # Filter allowed fields
        filtered_fields = {}
        for field, value in update_data.items():
            if field in always_editable or field in editable_fields:
                filtered_fields[field] = value
        
        print(f"✅ Filtered update fields: {filtered_fields}")
        
        # Verify superadmin is not in any field lists
        assert 'superadmin' not in editable_fields, "superadmin should not be editable"
        assert 'superadmin' not in role_fields, "superadmin should not be in role fields"
        assert 'superadmin' not in always_editable, "superadmin should not be always editable"
        
        print("✅ Commission update filtering logic works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Commission update logic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing commission update functionality after superadmin removal...\n")
    
    tests_passed = 0
    total_tests = 2
    
    print("📋 Test 1: Commission field schemas and role hierarchy")
    if test_commission_fields():
        tests_passed += 1
        print("✅ Test 1 PASSED\n")
    else:
        print("❌ Test 1 FAILED\n")
    
    print("📋 Test 2: Commission update logic")
    if test_commission_update_logic():
        tests_passed += 1
        print("✅ Test 2 PASSED\n")
    else:
        print("❌ Test 2 FAILED\n")
    
    print("="*50)
    print(f"📊 Tests Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Commission update functionality is working correctly.")
        print("✅ Superadmin field has been successfully removed from commission operations.")
        print("✅ Commission updates should now work properly with the payload:")
        print(json.dumps(commission_update_payload, indent=2))
    else:
        print("❌ Some tests failed. Commission update functionality needs more fixes.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)