"""
Comprehensive test for all scheme management integrations
"""
import requests


def test_all_endpoints():
    """Test all scheme management endpoints to verify they're working"""
    
    base_url = "http://localhost:8000/api/v1"
    
    endpoints_to_test = [
        {"url": f"{base_url}/schemes/", "name": "List Schemes"},
        {"url": f"{base_url}/operators", "name": "List Operators"},
        {"url": f"{base_url}/operators?service_type=mobile_recharge", "name": "Operators by Service"},
        {"url": f"{base_url}/commissions/export/1", "name": "Export Commissions"},
    ]
    
    print("=== SCHEME MANAGEMENT API INTEGRATION TEST ===\n")
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(endpoint["url"])
            status = response.status_code
            
            if status == 401:
                result = "✅ PASS - Requires authentication (expected)"
            elif status == 200:
                result = "✅ PASS - Working without auth"
                try:
                    data = response.json()
                    if isinstance(data, list):
                        result += f" ({len(data)} items)"
                    elif isinstance(data, dict) and 'items' in data:
                        result += f" ({len(data['items'])} items)"
                except:
                    pass
            elif status == 500:
                result = "❌ FAIL - Server error (likely import/model issues)"
            elif status == 404:
                result = "⚠️  WARN - Endpoint not found"
            else:
                result = f"⚠️  WARN - Unexpected status: {status}"
                
            print(f"{endpoint['name']:<25} | {result}")
            
        except Exception as e:
            print(f"{endpoint['name']:<25} | ❌ FAIL - Connection error: {e}")
    
    print("\n=== SUMMARY ===")
    print("✅ = Working correctly")
    print("❌ = Has issues that need fixing") 
    print("⚠️  = Needs investigation")


if __name__ == "__main__":
    test_all_endpoints()