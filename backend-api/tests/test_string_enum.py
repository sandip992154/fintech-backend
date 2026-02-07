#!/usr/bin/env python3
"""
Test using enum values directly
"""
from services.models.scheme_models import ServiceOperator
from database.database import SessionLocal

db = SessionLocal()

try:
    # Try to create a single operator using the string value directly
    operator = ServiceOperator(
        name="Test String Value",
        service_type="mobile_recharge",  # Use string directly
        is_active=True
    )
    
    db.add(operator)
    db.commit()
    
    print("✓ Successfully created operator with string value")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    db.rollback()
    
finally:
    db.close()