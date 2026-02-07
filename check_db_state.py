#!/usr/bin/env python3
"""
Check database state and verify user and scheme data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend-api'))

from database.database import SessionLocal
from services.models.models import User, Role
from services.models.scheme_models import Scheme

def check_db_state():
    """Check current database state"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking database state...\n")
        
        # Check users
        users = db.query(User).all()
        print(f"📋 Total Users: {len(users)}")
        for user in users:
            print(f"  • ID: {user.id}, Code: {user.user_code}, Name: {user.full_name}, Active: {user.is_active}")
        
        # Check roles
        roles = db.query(Role).all()
        print(f"\n📋 Total Roles: {len(roles)}")
        for role in roles:
            print(f"  • ID: {role.id}, Name: {role.name}, Desc: {role.description}")
        
        # Check schemes
        schemes = db.query(Scheme).all()
        print(f"\n📋 Total Schemes: {len(schemes)}")
        for scheme in schemes:
            print(f"  • ID: {scheme.id}, Name: {scheme.name}, Owner: {scheme.owner_id}, Created By: {scheme.created_by}, Role: {scheme.created_by_role}")
        
        # Check if superadmin exists
        superadmin = db.query(User).filter(User.user_code == "BANDSA000001").first()
        if superadmin:
            print(f"\n✅ Superadmin found: ID={superadmin.id}, Role: {superadmin.role_id}")
        else:
            print(f"\n❌ Superadmin (BANDSA000001) not found!")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_db_state()
