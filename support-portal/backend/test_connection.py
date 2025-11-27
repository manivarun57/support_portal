import requests
import time

print("Testing backend connection...")

# Wait a bit for server to be ready
time.sleep(2)

try:
    # Test health endpoint
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"✅ Health check: {response.status_code} - {response.json()}")
    
    # Test dashboard metrics
    response = requests.get("http://localhost:8000/dashboard/metrics", 
                          headers={"X-User-Id": "demo-user"}, timeout=5)
    print(f"✅ Dashboard metrics: {response.status_code} - {response.json()}")
    
    print("🎉 Backend is working correctly!")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend server at localhost:8000")
    print("Make sure the backend is running")
except Exception as e:
    print(f"❌ Error testing backend: {e}")

input("Press Enter to continue...")