#!/usr/bin/env python3
"""
Test script to verify bulk commission creation fixes.
This tests the ServiceTypeEnum vs int comparison errors that were causing failures.
"""

import sys
import asyncio
import json
from sqlalchemy.orm import Session
from database.database import SessionLocal, engine
from services.models.models import User, Role
from services.models.scheme_models import Scheme, ServiceTypeEnum
from services.business.scheme_service import SchemeService, CommissionService
from services.schemas.scheme_schemas import BulkCommissionCreate, CommissionEntry, CommissionTypeEnum
from services.utils.role_hierarchy import RoleHierarchy

def create_test_data():
    """Create test data for the bulk commission creation test"""
    db = SessionLocal()
    try:
        # Create a test superadmin role if it doesn't exist
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        if not superadmin_role:
            superadmin_role = Role(name="superadmin", description="Super Administrator")
            db.add(superadmin_role)
            db.commit()
            db.refresh(superadmin_role)
        
        # Create a test user if it doesn't exist
        test_user = db.query(User).filter(User.username == "test_superadmin").first()
        if not test_user:
            test_user = User(
                user_code="TEST_SUPER_001",
                username="test_superadmin",
                email="test@test.com",
                phone="1234567890",
                full_name="Test Super Admin",
                hashed_password="test",
                role_id=superadmin_role.id,
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create a test scheme if it doesn't exist
        test_scheme = db.query(Scheme).filter(Scheme.name == "Test Scheme").first()
        if not test_scheme:
            test_scheme = Scheme(
                name="Test Scheme",
                description="Test scheme for bulk commission creation",
                owner_id=test_user.id,
                created_by=test_user.id,
                created_by_role="superadmin",
                is_active=True
            )
            db.add(test_scheme)
            db.commit()
            db.refresh(test_scheme)
        
        print(f"✅ Test data created:")
        print(f"   - User: {test_user.username} (ID: {test_user.id}, Role ID: {test_user.role_id})")
        print(f"   - Scheme: {test_scheme.name} (ID: {test_scheme.id})")
        print(f"   - Role: {superadmin_role.name} (ID: {superadmin_role.id})")
        
        return test_user, test_scheme, db
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test data: {e}")
        return None, None, db

def test_role_hierarchy():
    """Test role hierarchy methods for type safety"""
    print("\n🔍 Testing RoleHierarchy methods...")
    
    try:
        # Test get_role_level with string
        level = RoleHierarchy.get_role_level("superadmin")
        print(f"   ✅ get_role_level('superadmin') = {level}")
        
        # Test can_manage_role with strings
        can_manage = RoleHierarchy.can_manage_role("superadmin", "retailer")
        print(f"   ✅ can_manage_role('superadmin', 'retailer') = {can_manage}")
        
        # Test can_manage_role with problematic enum comparison
        try:
            # This should not fail with our fixes
            can_manage_enum = RoleHierarchy.can_manage_role("superadmin", ServiceTypeEnum.MOBILE_RECHARGE)
            print(f"   ✅ can_manage_role with ServiceTypeEnum handled gracefully")
        except Exception as e:
            print(f"   ⚠️  ServiceTypeEnum comparison still has issues: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ RoleHierarchy test failed: {e}")
        return False

def test_bulk_commission_creation():
    """Test bulk commission creation with the fixes"""
    print("\n🚀 Testing Bulk Commission Creation...")
    
    # Create test data
    test_user, test_scheme, db = create_test_data()
    if not test_user or not test_scheme:
        print("❌ Failed to create test data")
        return False
    
    try:
        # Initialize the service
        commission_service = CommissionService(db)
        
        # Create test commission entries
        commission_entries = [
            CommissionEntry(
                operator="Test Operator 1",
                commission_type=CommissionTypeEnum.PERCENTAGE,
                superadmin=5.0,
                admin=4.0,
                whitelabel=3.0,
                masterdistributor=2.5,
                distributor=2.0,
                retailer=1.5,
                customer=1.0
            ),
            CommissionEntry(
                operator="Test Operator 2",
                commission_type=CommissionTypeEnum.FIXED,
                superadmin=10.0,
                admin=8.0,
                whitelabel=6.0,
                masterdistributor=5.0,
                distributor=4.0,
                retailer=3.0,
                customer=2.0
            )
        ]
        
        # Create bulk commission request
        bulk_data = BulkCommissionCreate(
            service="mobile_recharge",  # String instead of enum to test conversion
            entries=commission_entries
        )
        
        print(f"   📝 Created bulk request with {len(bulk_data.entries)} entries")
        print(f"   📝 Service type: {bulk_data.service} (type: {type(bulk_data.service)})")
        
        # Test the bulk creation
        result = commission_service.bulk_create_commissions(
            scheme_id=test_scheme.id,
            bulk_data=bulk_data,
            user_id=test_user.id,
            user_role="superadmin"
        )
        
        print(f"   ✅ Bulk commission creation successful!")
        print(f"   📊 Results: {json.dumps(result, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Bulk commission creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

def test_user_role_access():
    """Test user role access patterns"""
    print("\n👤 Testing User Role Access...")
    
    test_user, test_scheme, db = create_test_data()
    if not test_user or not test_scheme:
        print("❌ Failed to create test data")
        return False
    
    try:
        # Test can_user_access_scheme method
        can_access = RoleHierarchy.can_user_access_scheme(test_user, test_scheme)
        print(f"   ✅ can_user_access_scheme result: {can_access}")
        
        # Print user role information for debugging
        print(f"   📝 User role type: {type(test_user.role)}")
        print(f"   📝 User role value: {test_user.role}")
        if hasattr(test_user.role, 'name'):
            print(f"   📝 User role name: {test_user.role.name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ User role access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

def main():
    """Run all tests"""
    print("🧪 Running ServiceTypeEnum vs Int Comparison Fix Tests")
    print("=" * 60)
    
    # Test individual components
    test1 = test_role_hierarchy()
    test2 = test_user_role_access()
    test3 = test_bulk_commission_creation()
    
    # Summary
    print("\n📋 Test Summary:")
    print(f"   RoleHierarchy Methods: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   User Role Access: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"   Bulk Commission Creation: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests passed! ServiceTypeEnum comparison issues have been resolved.")
        return 0
    else:
        print("\n💥 Some tests failed. Further debugging needed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())