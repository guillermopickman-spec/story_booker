#!/usr/bin/env python3
"""
Simple test script to check backend connectivity
"""
import requests
import json

# Test health endpoint
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Health endpoint: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Health endpoint error: {e}")

# Test basic generate image endpoint
try:
    response = requests.post("http://localhost:8000/generate-image", 
                           json={"prompt": "test"}, 
                           timeout=5)
    print(f"Generate image endpoint: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Generate image endpoint error: {e}")

# Test generate image with description endpoint
try:
    response = requests.post("http://localhost:8000/generate-image-with-description", 
                           json={"character_name": "Test", "prompt": "test", "style": "pixar"}, 
                           timeout=5)
    print(f"Generate image with description endpoint: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Generate image with description endpoint error: {e}")

print("Test completed")