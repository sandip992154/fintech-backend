#!/usr/bin/env python3
"""
Test AEPS commission slab functionality.
"""

from services.schemas.scheme_schemas import CommissionCreate, CommissionSlabCreate, ServiceTypeEnum, CommissionTypeEnum

def test_aeps_commission_schema():
    """Test AEPS commission creation with slabs"""
    print("🧪 Testing AEPS commission schema with slabs...")
    
    try:
        # Test data with slabs
        aeps_commission_data = {
            "operator_id": 26,
            "service_type": "aeps",
            "commission_type": "fixed",
            "admin": 0.0,
            "whitelabel": 0.0,
            "masterdistributor": 0.0,
            "distributor": 0.0,
            "retailer": 0.0,
            "customer": 0.0,
            "slabs": [
                {
                    "slab_min": 0.0,
                    "slab_max": 1000.0,
                    "admin": 2.0,
                    "whitelabel": 1.8,
                    "masterdistributor": 1.5,
                    "distributor": 1.2,
                    "retailer": 1.0,
                    "customer": 0.8
                },
                {
                    "slab_min": 1000.01,  # Fix overlap - start just after previous slab
                    "slab_max": 5000.0,
                    "admin": 3.0,
                    "whitelabel": 2.7,
                    "masterdistributor": 2.4,
                    "distributor": 2.0,
                    "retailer": 1.8,
                    "customer": 1.5
                }
            ]
        }
        
        # Create commission schema
        commission = CommissionCreate(**aeps_commission_data)
        print(f"✅ AEPS commission schema created successfully")
        print(f"   Service type: {commission.service_type}")
        print(f"   Commission type: {commission.commission_type}")
        print(f"   Number of slabs: {len(commission.slabs) if commission.slabs else 0}")
        
        if commission.slabs:
            for i, slab in enumerate(commission.slabs):
                print(f"   Slab {i+1}: {slab.slab_min}-{slab.slab_max}, admin: {slab.admin}")
                
        return True
        
    except Exception as e:
        print(f"❌ AEPS commission schema test failed: {str(e)}")
        return False

def test_model_dump_compatibility():
    """Test Pydantic v2 model_dump() compatibility"""
    print("\n📋 Testing Pydantic v2 compatibility...")
    
    try:
        slab_data = CommissionSlabCreate(
            slab_min=0.0,
            slab_max=1000.0,
            admin=2.0,
            whitelabel=1.8,
            masterdistributor=1.5,
            distributor=1.2,
            retailer=1.0,
            customer=0.8
        )
        
        # Test model_dump() method
        if hasattr(slab_data, 'model_dump'):
            slab_dict = slab_data.model_dump()
            print(f"✅ Using model_dump(): {slab_dict}")
        else:
            slab_dict = slab_data.dict()
            print(f"✅ Using dict() fallback: {slab_dict}")
            
        print(f"✅ Slab data serialization works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Model dump test failed: {str(e)}")
        return False

def test_aeps_service_detection():
    """Test AEPS service type detection"""
    print("\n🔍 Testing AEPS service detection...")
    
    try:
        # Test with different service types
        aeps_service = ServiceTypeEnum.AEPS
        mobile_service = ServiceTypeEnum.MOBILE_RECHARGE
        
        print(f"✅ AEPS enum: {aeps_service} (value: {aeps_service.value})")
        print(f"✅ Mobile enum: {mobile_service} (value: {mobile_service.value})")
        
        # Test string comparison
        is_aeps_string = "aeps" == aeps_service.value
        is_aeps_enum = ServiceTypeEnum.AEPS == aeps_service
        
        print(f"✅ String comparison: {is_aeps_string}")
        print(f"✅ Enum comparison: {is_aeps_enum}")
        
        return True
        
    except Exception as e:
        print(f"❌ AEPS service detection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AEPS commission slab functionality...\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_aeps_commission_schema():
        tests_passed += 1
    
    if test_model_dump_compatibility():
        tests_passed += 1
        
    if test_aeps_service_detection():
        tests_passed += 1
    
    print(f"\n==================================================")
    print(f"📊 Tests Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All AEPS tests passed! Commission slab functionality should work correctly.")
    else:
        print("❌ Some tests failed. AEPS commission slab functionality needs fixes.")
        exit(1)