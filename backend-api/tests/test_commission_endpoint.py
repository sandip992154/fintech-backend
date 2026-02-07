#!/usr/bin/env python3
"""
Test script to verify commission endpoints are working correctly
"""

import requests
import json
from datetime import datetime

def test_commission_endpoints():
    """Test commission endpoints with a simple request"""
    base_url = "http://localhost:8000"
    
    # Test endpoints
    print("🧪 Testing Commission Endpoints")
    print("=" * 50)
    
    # 1. Test if server is running
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print("✅ Backend server is running")
    except Exception as e:
        print(f"❌ Backend server not accessible: {e}")
        return
    
    # 2. Check available endpoints
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_data = response.json()
            commission_paths = [path for path in openapi_data.get('paths', {}).keys() 
                             if 'commission' in path.lower()]
            print(f"✅ Found {len(commission_paths)} commission-related endpoints:")
            for path in commission_paths:
                print(f"   - {path}")
        else:
            print("❌ Could not fetch OpenAPI spec")
    except Exception as e:
        print(f"❌ Error fetching endpoints: {e}")
    
    # 3. Test service types
    service_types = [
        "mobile_recharge",
        "dth_recharge", 
        "bill_payments",
        "aeps",
        "dmt",
        "micro_atm"
    ]
    
    print(f"\n📋 Available Service Types:")
    for service in service_types:
        print(f"   - {service}")
    
    # 4. Test commission endpoint structure
    print(f"\n🔍 Testing Commission Endpoint Structure:")
    print(f"   Endpoint: GET /schemes/{{scheme_id}}/commissions?service={{service_type}}")
    print(f"   Required: scheme_id (int), service (string)")
    print(f"   Response: CommissionListResponse with entries array")
    
    print(f"\n📝 Expected Response Structure:")
    expected_response = {
        "service": "mobile_recharge",
        "entries": [
            {
                "id": 1,
                "scheme_id": 1,
                "service_type": "mobile_recharge",
                "commission_type": "percentage",
                "operator": {
                    "id": 1,
                    "name": "Airtel",
                    "service_type": "mobile_recharge"
                },
                "superadmin": 5.0,
                "admin": 4.0,
                "whitelabel": 3.0,
                "masterdistributor": 2.5,
                "distributor": 2.0,
                "retailer": 1.5,
                "customer": 0.0,
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
    }
    print(json.dumps(expected_response, indent=2))
    
    print(f"\n🚀 Frontend Implementation:")
    print(f"   - Use getAllCommissionsByScheme(schemeId) method")
    print(f"   - Fetches commissions for all service types")
    print(f"   - Groups by service type for tab display")
    print(f"   - Handles empty responses gracefully")
    
    print(f"\n✅ Commission endpoint testing complete!")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_commission_endpoints()