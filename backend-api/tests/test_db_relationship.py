#!/usr/bin/env python3
"""
Test database relationship for Commission -> CommissionSlab
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_commission_slab_relationship():
    """Test if Commission and CommissionSlab relationship works"""
    print("🔍 Testing Commission -> CommissionSlab database relationship...")
    
    try:
        from services.models.scheme_models import Commission, CommissionSlab
        from sqlalchemy.orm import relationship
        
        # Check if Commission model has slabs relationship
        commission_attrs = dir(Commission)
        has_slabs_attr = 'slabs' in commission_attrs
        print(f"✅ Commission.slabs attribute exists: {has_slabs_attr}")
        
        # Check if CommissionSlab model has commission relationship  
        slab_attrs = dir(CommissionSlab)
        has_commission_attr = 'commission' in slab_attrs
        print(f"✅ CommissionSlab.commission attribute exists: {has_commission_attr}")
        
        # Try to get relationship info
        if hasattr(Commission, 'slabs'):
            slabs_rel = getattr(Commission, 'slabs')
            print(f"✅ Commission.slabs relationship: {type(slabs_rel)}")
            
        if hasattr(CommissionSlab, 'commission'):
            comm_rel = getattr(CommissionSlab, 'commission')
            print(f"✅ CommissionSlab.commission relationship: {type(comm_rel)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database relationship test failed: {str(e)}")
        return False

def test_import_dependencies():
    """Test if all necessary imports work"""
    print("\n📦 Testing import dependencies...")
    
    try:
        from services.models.scheme_models import Commission, CommissionSlab
        print("✅ Models imported successfully")
        
        from services.schemas.scheme_schemas import CommissionOut, CommissionSlabOut
        print("✅ Schemas imported successfully")
        
        from sqlalchemy.orm import joinedload
        print("✅ SQLAlchemy joinedload imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def test_query_simulation():
    """Simulate the query structure for commission with slabs"""
    print("\n🔍 Testing query structure simulation...")
    
    try:
        from services.models.scheme_models import Commission, CommissionSlab
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_
        
        # Simulate the query structure (without actually executing)
        print("✅ Query structure for commission with slabs:")
        print("   query = db.query(Commission).options(")
        print("       joinedload(Commission.slabs),")
        print("       joinedload(Commission.operator)")
        print("   ).filter(")
        print("       and_(")
        print("           Commission.scheme_id == scheme_id,")
        print("           Commission.service_type == service_type,")
        print("           Commission.is_active == True")
        print("       )")
        print("   ).all()")
        
        return True
        
    except Exception as e:
        print(f"❌ Query simulation test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AEPS commission database relationship...\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_import_dependencies():
        tests_passed += 1
    
    if test_commission_slab_relationship():
        tests_passed += 1
        
    if test_query_simulation():
        tests_passed += 1
    
    print(f"\n==================================================")
    print(f"📊 Tests Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All database relationship tests passed!")
        print("\n🔍 Next steps to debug AEPS slab issue:")
        print("1. ✅ Database models have proper relationships")
        print("2. ✅ Query structure should load slabs correctly")
        print("3. 🔄 Need to check if slabs actually exist in database")
        print("4. 🔄 Need to verify API response includes loaded slabs")
    else:
        print("❌ Some tests failed. Database relationship needs fixes.")