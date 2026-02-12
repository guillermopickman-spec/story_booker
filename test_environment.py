#!/usr/bin/env python3
"""
Simple test script to verify frontend-backend communication
"""

import requests
import json

def test_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Story Booker Backend...")
    
    # Test basic info
    try:
        response = requests.get(f"{base_url}/")
        print(f"SUCCESS Basic info: {response.json()}")
    except Exception as e:
        print(f"ERROR Basic info failed: {e}")
        return False
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"SUCCESS Health check: {response.json()}")
    except Exception as e:
        print(f"ERROR Health check failed: {e}")
        return False
    
    # Test image generation
    try:
        response = requests.post(f"{base_url}/generate-image", 
                               json={"prompt": "test character"})
        result = response.json()
        print(f"SUCCESS Image generation: {result['success']} - {result['message']}")
    except Exception as e:
        print(f"ERROR Image generation failed: {e}")
        return False
    
    # Test description generation
    try:
        response = requests.post(f"{base_url}/generate-description", 
                               json={"prompt": "test character"})
        result = response.json()
        print(f"SUCCESS Description generation: {result['success']} - {result['message']}")
    except Exception as e:
        print(f"ERROR Description generation failed: {e}")
        return False
    
    return True

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"SUCCESS Frontend accessible: Status {response.status_code}")
        return True
    except Exception as e:
        print(f"ERROR Frontend not accessible: {e}")
        return False

def main():
    """Main test function"""
    print("=== Story Booker Environment Test ===\n")
    
    backend_ok = test_backend()
    print()
    frontend_ok = test_frontend()
    
    print(f"\n=== Results ===")
    print(f"Backend: {'SUCCESS Working' if backend_ok else 'ERROR Failed'}")
    print(f"Frontend: {'SUCCESS Working' if frontend_ok else 'ERROR Failed'}")
    
    if backend_ok and frontend_ok:
        print("\nSUCCESS Both frontend and backend are working!")
        return True
    else:
        print("\nERROR Some components are not working properly.")
        return False

if __name__ == "__main__":
    main()