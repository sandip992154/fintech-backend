#!/usr/bin/env python3
"""
Test commission hierarchy with 0.0 defaults
"""

from services.utils.role_hierarchy import RoleHierarchy

def test_zero_defaults():
    """Test commission hierarchy validation with 0.0 defaults"""
    print("🧪 Testing Commission Hierarchy with 0.0 Defaults")
    print("=" * 60)
    
    # Test data that mimics what comes from CommissionEntry with defaults
    test_data = {
        "superadmin": 0.0,  # Default value from schema
        "admin": 1.0,       # User-specified value
        "whitelabel": 0.8,
        "masterdistributor": 0.7,
        "distributor": 0.4,
        "retailer": 0.3,
        "customer": 0.1
    }
    
    print(f"📝 Test data: {test_data}")
    result = RoleHierarchy.validate_commission_hierarchy(test_data)
    print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test data with only zeros at the top
    test_data_2 = {
        "superadmin": 0.0,
        "admin": 0.0,
        "whitelabel": 2.0,
        "masterdistributor": 1.5,
        "distributor": 1.0,
        "retailer": 0.5,
        "customer": 0.1
    }
    
    print(f"\n📝 Test data 2 (zero superadmin & admin): {test_data_2}")
    result_2 = RoleHierarchy.validate_commission_hierarchy(test_data_2)
    print(f"Result: {'✅ PASS' if result_2 else '❌ FAIL'}")
    
    return result and result_2

if __name__ == "__main__":
    test_zero_defaults()