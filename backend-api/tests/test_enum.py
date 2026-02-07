#!/usr/bin/env python3
"""
Test enum creation
"""
from services.models.scheme_models import ServiceTypeEnum, ServiceOperator
from database.database import SessionLocal

db = SessionLocal()

try:
    print("Testing enum values:")
    print(f"ServiceTypeEnum.MOBILE_RECHARGE = {ServiceTypeEnum.MOBILE_RECHARGE}")
    print(f"ServiceTypeEnum.MOBILE_RECHARGE value = {ServiceTypeEnum.MOBILE_RECHARGE.value}")
    
    # Try to create a single operator
    operator = ServiceOperator(
        name="Test Airtel",
        service_type=ServiceTypeEnum.MOBILE_RECHARGE,
        is_active=True
    )
    
    db.add(operator)
    db.commit()
    
    print("✓ Successfully created operator")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    db.rollback()
    
finally:
    db.close()