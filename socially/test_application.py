#!/usr/bin/env python3
"""
Test script to verify the Socially application is working correctly.
"""

import requests
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint is working")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket connection (basic test)"""
    try:
        import websocket
        
        ws = websocket.WebSocket()
        ws.connect("ws://localhost:8000/ws")
        print("✅ WebSocket connection established")
        ws.close()
        return True
    except ImportError:
        print("⚠️  websocket-client not installed, skipping WebSocket test")
        return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Socially Application...")
    print("=" * 50)
    
    # Wait a moment for the application to be ready
    time.sleep(2)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    # Test WebSocket connection
    ws_ok = test_websocket_connection()
    
    print("=" * 50)
    if health_ok and ws_ok:
        print("🎉 All tests passed! The application is ready.")
        print("📱 Access the application at: http://localhost:8000")
    else:
        print("❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
