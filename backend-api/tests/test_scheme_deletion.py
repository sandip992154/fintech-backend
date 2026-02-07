#!/usr/bin/env python3
"""
Test scheme deletion functionality
"""

import sys
from database.database import SessionLocal
from services.models.models import User, Role
from services.models.scheme_models import Scheme
from services.business.scheme_service import SchemeService

def test_scheme_deletion():
    """Test that scheme deletion properly implements soft delete"""
    print("🧪 Testing Scheme Deletion Functionality")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get existing test data
        test_user = db.query(User).filter(User.username == "test_superadmin").first()
        if not test_user:
            print("❌ Test user not found. Run test_bulk_commission_fix.py first.")
            return False
        
        # Initialize the service
        scheme_service = SchemeService(db)
        
        # Create a test scheme for deletion
        from services.schemas.scheme_schemas import SchemeCreate
        
        scheme_data = SchemeCreate(
            name="Test Deletion Scheme",
            description="This scheme will be deleted for testing"
        )
        
        # Create the scheme
        new_scheme = scheme_service.create_scheme(
            scheme_data,
            created_by=test_user.id,
            creator_role="superadmin",
            owner_id=test_user.id
        )
        
        print(f"📝 Created test scheme: {new_scheme.name} (ID: {new_scheme.id})")
        
        # Verify scheme is in the listing (active schemes)
        schemes_before, total_before = scheme_service.get_schemes(
            current_user_id=test_user.id,
            current_user_role="superadmin"
        )
        
        scheme_ids_before = [s.id for s in schemes_before]
        print(f"📋 Schemes before deletion: {len(schemes_before)} total")
        print(f"   Scheme {new_scheme.id} in list: {'✅ YES' if new_scheme.id in scheme_ids_before else '❌ NO'}")
        
        # Delete the scheme
        print(f"🗑️  Deleting scheme {new_scheme.id}...")
        success = scheme_service.delete_scheme(new_scheme.id)
        print(f"   Deletion success: {'✅ YES' if success else '❌ NO'}")
        
        # Verify scheme is no longer in the listing (active schemes only)
        schemes_after, total_after = scheme_service.get_schemes(
            current_user_id=test_user.id,
            current_user_role="superadmin"
        )
        
        scheme_ids_after = [s.id for s in schemes_after]
        print(f"📋 Schemes after deletion: {len(schemes_after)} total")
        print(f"   Scheme {new_scheme.id} in list: {'❌ NO' if new_scheme.id not in scheme_ids_after else '✅ YES (PROBLEM!)'}")
        
        # Verify scheme still exists in database but is inactive
        deleted_scheme = db.query(Scheme).filter(Scheme.id == new_scheme.id).first()
        if deleted_scheme:
            print(f"💾 Scheme in database: ✅ YES (is_active: {deleted_scheme.is_active})")
            soft_delete_working = not deleted_scheme.is_active
        else:
            print(f"💾 Scheme in database: ❌ NO (hard deleted)")
            soft_delete_working = False
        
        # Verify we can retrieve inactive schemes explicitly
        schemes_inactive, total_inactive = scheme_service.get_schemes(
            current_user_id=test_user.id,
            current_user_role="superadmin",
            is_active=False
        )
        
        inactive_ids = [s.id for s in schemes_inactive]
        print(f"📋 Inactive schemes: {len(schemes_inactive)} total")
        print(f"   Deleted scheme in inactive list: {'✅ YES' if new_scheme.id in inactive_ids else '❌ NO'}")
        
        # Test results
        test_results = {
            "scheme_created": new_scheme is not None,
            "deletion_success": success,
            "removed_from_active_list": new_scheme.id not in scheme_ids_after,
            "soft_delete_working": soft_delete_working,
            "found_in_inactive_list": new_scheme.id in inactive_ids
        }
        
        print(f"\n📊 Test Results:")
        for test_name, result in test_results.items():
            print(f"   {test_name}: {'✅ PASS' if result else '❌ FAIL'}")
        
        all_passed = all(test_results.values())
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    result = test_scheme_deletion()
    sys.exit(0 if result else 1)