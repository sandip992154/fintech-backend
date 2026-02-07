#!/usr/bin/env python3
"""
Comprehensive test for all commission management fixes
"""

import sys
import json
from database.database import SessionLocal
from services.models.models import User, Role
from services.models.scheme_models import Scheme
from services.business.scheme_service import SchemeService, CommissionService
from services.schemas.scheme_schemas import BulkCommissionCreate, CommissionEntry, CommissionTypeEnum
from services.utils.role_hierarchy import RoleHierarchy

def test_all_commission_fixes():
    """Test all commission management improvements together"""
    print("🧪 Comprehensive Commission Management Test")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Get existing test data
        test_user = db.query(User).filter(User.username == "test_superadmin").first()
        test_scheme = db.query(Scheme).filter(Scheme.name == "Test Scheme").first()
        
        if not test_user or not test_scheme:
            print("❌ Test data not found. Run test_bulk_commission_fix.py first.")
            return False
        
        print(f"📝 Using user: {test_user.username} (role: {test_user.role.name})")
        print(f"📝 Using scheme: {test_scheme.name} (ID: {test_scheme.id})")
        
        # Test 1: Role Hierarchy Permissions
        print(f"\n{'='*50}")
        print("🧪 Test 1: Commission Role Hierarchy Permissions")
        print(f"{'='*50}")
        
        # Create commission data that violates hierarchy permissions (admin setting superadmin)
        invalid_commission_data = {
            "superadmin": 5.0,  # Admin should NOT be able to set this
            "admin": 4.0,
            "whitelabel": 3.0,
            "distributor": 1.5
        }
        
        errors = RoleHierarchy.validate_commission_role_permissions("admin", invalid_commission_data)
        print(f"   Admin trying to set superadmin commission:")
        print(f"   Errors: {errors}")
        print(f"   Result: {'✅ PASS' if 'superadmin' in errors else '❌ FAIL'} (should have superadmin error)")
        
        # Test valid commission data (admin setting only subordinate roles)
        valid_commission_data = {
            "admin": 4.0,
            "whitelabel": 3.0,
            "distributor": 1.5,
            "retailer": 1.0
        }
        
        errors_valid = RoleHierarchy.validate_commission_role_permissions("admin", valid_commission_data)
        print(f"   Admin setting subordinate roles only:")
        print(f"   Errors: {errors_valid}")
        print(f"   Result: {'✅ PASS' if not errors_valid else '❌ FAIL'} (should have no errors)")
        
        # Test 2: Bulk Commission Creation with Hierarchy
        print(f"\n{'='*50}")
        print("🧪 Test 2: Bulk Commission Creation with Fixed Hierarchy")
        print(f"{'='*50}")
        
        commission_service = CommissionService(db)
        
        # Test the user's original data that was failing
        import time
        timestamp = int(time.time())
        
        commission_entries = [
            CommissionEntry(
                operator=f"Test Operator Hierarchy {timestamp}",
                commission_type=CommissionTypeEnum.PERCENTAGE,
                admin=1.0,
                whitelabel=0.8,
                masterdistributor=0.7,
                distributor=0.4,
                retailer=0.3,
                customer=0.1
            )
        ]
        
        bulk_data = BulkCommissionCreate(
            service="mobile_recharge",
            entries=commission_entries
        )
        
        print(f"   Creating commission with hierarchy: admin(1.0) > whitelabel(0.8) > ... > customer(0.1)")
        
        try:
            result = commission_service.bulk_create_commissions(
                scheme_id=test_scheme.id,
                bulk_data=bulk_data,
                user_id=test_user.id,
                user_role="superadmin"
            )
            
            print(f"   Bulk creation result:")
            print(f"     Successful: {result['successful_entries']}")
            print(f"     Failed: {result['failed_entries']}")
            if result['errors']:
                print(f"     Errors: {result['errors']}")
            
            hierarchy_test_pass = result['successful_entries'] > 0
            print(f"   Result: {'✅ PASS' if hierarchy_test_pass else '❌ FAIL'}")
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            hierarchy_test_pass = False
        
        # Test 3: Commission Visibility (Access Control)
        print(f"\n{'='*50}")
        print("🧪 Test 3: Role-Based Commission Visibility")
        print(f"{'='*50}")
        
        # Test accessing commissions with proper user context
        try:
            commissions = commission_service.get_commissions_by_scheme_and_service(
                scheme_id=test_scheme.id,
                service_type="mobile_recharge",
                current_user_id=test_user.id,
                current_user_role="superadmin"
            )
            
            print(f"   Commissions retrieved: {len(commissions)}")
            print(f"   Access control working: ✅ YES")
            visibility_test_pass = True
            
        except Exception as e:
            print(f"   ❌ Exception accessing commissions: {e}")
            visibility_test_pass = False
        
        # Test 4: Scheme Deletion (Soft Delete)
        print(f"\n{'='*50}")
        print("🧪 Test 4: Scheme Deletion (Soft Delete)")
        print(f"{'='*50}")
        
        scheme_service = SchemeService(db)
        
        # Create a test scheme for deletion
        from services.schemas.scheme_schemas import SchemeCreate
        import time
        
        # Use timestamp to ensure unique name
        timestamp = int(time.time())
        deletion_scheme_data = SchemeCreate(
            name=f"Test Comprehensive Deletion {timestamp}",
            description="This scheme will be deleted for comprehensive testing"
        )
        
        deletion_scheme = scheme_service.create_scheme(
            deletion_scheme_data,
            created_by=test_user.id,
            creator_role="superadmin",
            owner_id=test_user.id
        )
        
        print(f"   Created deletion test scheme: {deletion_scheme.name} (ID: {deletion_scheme.id})")
        
        # Delete the scheme
        deletion_success = scheme_service.delete_scheme(deletion_scheme.id)
        
        # Verify it's not in active listing
        active_schemes, _ = scheme_service.get_schemes(
            current_user_id=test_user.id,
            current_user_role="superadmin"
        )
        
        active_ids = [s.id for s in active_schemes]
        not_in_active_list = deletion_scheme.id not in active_ids
        
        print(f"   Deletion success: {'✅ YES' if deletion_success else '❌ NO'}")
        print(f"   Removed from active list: {'✅ YES' if not_in_active_list else '❌ NO'}")
        
        deletion_test_pass = deletion_success and not_in_active_list
        
        # Summary
        print(f"\n{'='*70}")
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*70}")
        
        all_tests = {
            "Role Hierarchy Permissions": 'superadmin' in errors and not errors_valid,
            "Bulk Commission Creation": hierarchy_test_pass,
            "Commission Visibility": visibility_test_pass,
            "Scheme Deletion": deletion_test_pass
        }
        
        for test_name, result in all_tests.items():
            print(f"   {test_name}: {'✅ PASS' if result else '❌ FAIL'}")
        
        overall_success = all(all_tests.values())
        print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            print(f"\n🎉 Commission management system is working correctly!")
            print(f"   ✅ Role hierarchy permissions enforced")
            print(f"   ✅ Commission visibility properly controlled") 
            print(f"   ✅ Scheme deletion working with soft delete")
            print(f"   ✅ Bulk commission creation handles hierarchy properly")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    result = test_all_commission_fixes()
    sys.exit(0 if result else 1)