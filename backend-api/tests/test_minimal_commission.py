#!/usr/bin/env python3
"""
Minimal test to isolate the ServiceTypeEnum vs int comparison error.
"""

import sys
from sqlalchemy.orm import Session
from database.database import SessionLocal
from services.models.models import User, Role
from services.models.scheme_models import Scheme, ServiceTypeEnum
from services.business.scheme_service import CommissionService
from services.schemas.scheme_schemas import CommissionCreate, CommissionTypeEnum

def test_single_commission_creation():
    """Test individual commission creation to isolate the error"""
    print("🔬 Testing Individual Commission Creation...")
    
    db = SessionLocal()
    try:
        # Get existing test data
        test_user = db.query(User).filter(User.username == "test_superadmin").first()
        test_scheme = db.query(Scheme).filter(Scheme.name == "Test Scheme").first()
        
        if not test_user or not test_scheme:
            print("❌ Test data not found. Run the main test first.")
            return False
        
        print(f"📝 Using user: {test_user.username} (role: {test_user.role.name})")
        print(f"📝 Using scheme: {test_scheme.name} (ID: {test_scheme.id})")
        
        # Initialize commission service
        commission_service = CommissionService(db)
        
        # Create a simple commission
        commission_data = CommissionCreate(
            operator_id=1,  # Assuming operator exists
            service_type=ServiceTypeEnum.MOBILE_RECHARGE,  # Enum directly
            commission_type=CommissionTypeEnum.PERCENTAGE,
            superadmin=5.0,
            admin=4.0,
            whitelabel=3.0,
            masterdistributor=2.5,
            distributor=2.0,
            retailer=1.5,
            customer=1.0
        )
        
        print(f"📝 service_type: {commission_data.service_type} (type: {type(commission_data.service_type)})")
        print(f"📝 user_role: 'superadmin' (type: {type('superadmin')})")
        
        # This is where the error should occur
        print("🚀 Calling create_commission...")
        result = commission_service.create_commission(
            scheme_id=test_scheme.id,
            commission_data=commission_data,
            user_id=test_user.id,
            user_role="superadmin"  # String role
        )
        
        print(f"✅ Commission created successfully: {result.id}")
        return True
        
    except Exception as e:
        print(f"❌ Error in commission creation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

def main():
    """Run the minimal test"""
    print("🧪 Minimal ServiceTypeEnum Comparison Test")
    print("=" * 50)
    
    result = test_single_commission_creation()
    
    if result:
        print("\n✅ Test passed - individual commission creation works")
    else:
        print("\n❌ Test failed - issue isolated")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())