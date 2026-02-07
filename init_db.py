#!/usr/bin/env python3
"""
Initialize all database tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend-api'))

from database.database import engine, Base
from services.models.models import *  # Import all models
from services.models.scheme_models import *  # Import scheme models
from services.models.user_models import *  # Import user models

def init_db():
    """Create all tables that don't exist"""
    print("🚀 Initializing database tables...\n")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All database tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Tables in database ({len(tables)}):")
        for table in sorted(tables):
            print(f"  ✓ {table}")
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
    print("\n✅ Done!")
