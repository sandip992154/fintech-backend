#!/usr/bin/env python3
"""
Add sample scheme data to the database for testing
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend-api'))

from database.database import SessionLocal, engine, Base
from services.models.scheme_models import Scheme
from datetime import datetime

def add_sample_schemes():
    """Add sample schemes to database"""
    db = SessionLocal()
    
    try:
        # Check if schemes already exist
        existing_schemes = db.query(Scheme).count()
        if existing_schemes > 0:
            print(f"✅ {existing_schemes} schemes already exist in database")
            return
        
        # Sample schemes
        sample_schemes = [
            {
                "name": "Basic AEPS Scheme",
                "description": "Basic AEPS (Aadhaar Enabled Payment System) scheme for retailers",
                "is_active": True,
                "owner_id": 1,  # Superadmin
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Premium AEPS Plus",
                "description": "Premium AEPS scheme with enhanced features and higher limits",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Micro ATM Standard",
                "description": "Standard Micro ATM service for cash withdrawal and deposits",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Money Transfer Basic",
                "description": "Basic money transfer scheme for domestic transfers",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Bill Payment Standard",
                "description": "Utility bill payment scheme supporting electricity, water, and telecom",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Pan Card Application",
                "description": "PAN (Permanent Account Number) card application processing",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "FASTag Service",
                "description": "FASTag highway toll payment system",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
            {
                "name": "Insurance Premium Basic",
                "description": "Basic insurance premium payment scheme",
                "is_active": True,
                "owner_id": 1,
                "created_by": 1,
                "created_by_role": "super_admin",
            },
        ]
        
        # Add schemes to database
        for scheme_data in sample_schemes:
            scheme = Scheme(**scheme_data)
            db.add(scheme)
        
        db.commit()
        print(f"✅ Successfully added {len(sample_schemes)} sample schemes to database")
        
        # Display added schemes
        all_schemes = db.query(Scheme).all()
        print(f"\n📋 Total schemes in database: {len(all_schemes)}\n")
        for scheme in all_schemes:
            print(f"  • {scheme.name} - Active: {scheme.is_active}")
            print(f"    Description: {scheme.description[:60]}...")
        
    except Exception as e:
        print(f"❌ Error adding schemes: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Adding sample scheme data...\n")
    add_sample_schemes()
    print("\n✅ Done!")
