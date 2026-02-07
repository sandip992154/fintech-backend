#!/usr/bin/env python3
"""
Direct database test without using models
"""
from database.database import engine
from sqlalchemy import text

# Insert data directly with SQL
try:
    with engine.connect() as conn:
        # Test inserting with lowercase enum values
        result = conn.execute(text("""
            INSERT INTO service_operators (name, service_type, is_active, created_at, updated_at)
            VALUES ('Test Direct Airtel', 'mobile_recharge', true, NOW(), NOW())
            RETURNING id, name, service_type
        """))
        
        row = result.fetchone()
        print(f"✓ Successfully inserted operator: ID={row[0]}, Name='{row[1]}', Service='{row[2]}'")
        
        conn.commit()
        
except Exception as e:
    print(f"❌ Error: {str(e)}")