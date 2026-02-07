#!/usr/bin/env python3
"""
Test bulk commission creation with the user's actual data
"""

import sys
import json
from database.database import SessionLocal
from services.models.models import User, Role
from services.models.scheme_models import Scheme
from services.business.scheme_service import CommissionService
from services.schemas.scheme_schemas import BulkCommissionCreate, CommissionEntry, CommissionTypeEnum

def test_user_bulk_data():
    """Test bulk commission creation with user's actual data"""
    print("🧪 Testing User's Actual Bulk Commission Data")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get existing test data
        test_user = db.query(User).filter(User.username == "test_superadmin").first()
        test_scheme = db.query(Scheme).filter(Scheme.name == "Test Scheme").first()
        
        if not test_user or not test_scheme:
            print("❌ Test data not found. Run test_bulk_commission_fix.py first.")
            return False
        
        # Initialize the service
        commission_service = CommissionService(db)
        
        # User's actual data that was failing
        commission_entries = [
            CommissionEntry(
                operator="Airtel",
                commission_type=CommissionTypeEnum.PERCENTAGE,
                admin=1.0,
                whitelabel=0.8,
                masterdistributor=0.7,
                distributor=0.4,
                retailer=0.3,
                customer=0.1
            )
        ]
        
        # Create bulk commission request
        bulk_data = BulkCommissionCreate(
            service="mobile_recharge",
            entries=commission_entries
        )
        
        print(f"📝 Testing with commission data:")
        for entry in commission_entries:
            entry_dict = entry.dict()
            print(f"   {entry_dict['operator']}: {json.dumps({k: v for k, v in entry_dict.items() if k not in ['operator', 'commission_type']}, indent=2)}")
        
        # Test the bulk creation
        result = commission_service.bulk_create_commissions(
            scheme_id=test_scheme.id,
            bulk_data=bulk_data,
            user_id=test_user.id,
            user_role="superadmin"
        )
        
        print(f"\n📊 Results:")
        print(f"   Total entries: {result['total_entries']}")
        print(f"   Successful: {result['successful_entries']}")
        print(f"   Failed: {result['failed_entries']}")
        
        if result['errors']:
            print(f"   Errors:")
            for error in result['errors']:
                print(f"     - {error}")
        
        success = result['successful_entries'] > 0
        print(f"\n🎯 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    result = test_user_bulk_data()
    sys.exit(0 if result else 1)