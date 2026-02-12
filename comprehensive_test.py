#!/usr/bin/env python3
"""
Comprehensive Story Booker Integration Test
Tests both current capabilities and identifies areas for improvement
"""

import requests
import json
import time
import os

def test_current_backend():
    """Test the current backend capabilities"""
    print("=== Testing Current Backend Capabilities ===")
    
    base_url = "http://localhost:8000"
    
    # Test basic functionality
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Basic API: {response.json()['message']}")
    except Exception as e:
        print(f"✗ Basic API failed: {e}")
        return False
    
    # Test image generation (should work in test mode)
    try:
        response = requests.post(f"{base_url}/generate-image", 
                               json={"prompt": "test fantasy character"})
        result = response.json()
        if result['success']:
            print(f"✓ Image generation: {result['message']}")
            print(f"  - Image type: {result['image_data'][:50]}...")
        else:
            print(f"✗ Image generation failed: {result['message']}")
    except Exception as e:
        print(f"✗ Image generation error: {e}")
    
    # Test description generation (should work with Ollama)
    try:
        response = requests.post(f"{base_url}/generate-description", 
                               json={"prompt": "brave knight character"})
        result = response.json()
        if result['success']:
            print(f"✓ Description generation: {result['message']}")
            print(f"  - Description: {result['description'][:100]}...")
            print(f"  - Aspects: {list(result.get('modular_description', {}).keys())}")
        else:
            print(f"✗ Description generation failed: {result['message']}")
    except Exception as e:
        print(f"✗ Description generation error: {e}")
    
    return True

def test_ai_services():
    """Test external AI services"""
    print("\n=== Testing AI Services ===")
    
    # Test Ollama connection
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json()
        print(f"✓ Ollama running: {len(models.get('models', []))} models available")
        for model in models.get('models', [])[:3]:  # Show first 3 models
            print(f"  - {model['name']}")
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
    
    # Test ComfyUI connection
    try:
        response = requests.get("http://localhost:8188/system_stats")
        print(f"✓ ComfyUI running: {response.json()}")
    except Exception as e:
        print(f"✗ ComfyUI not accessible: {e}")
        print("  This is expected if ComfyUI is not installed yet")

def test_frontend():
    """Test frontend accessibility"""
    print("\n=== Testing Frontend ===")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✓ Frontend accessible (200 OK)")
        elif response.status_code == 404:
            print("✓ Frontend running but no specific route (404 normal for Next.js)")
        else:
            print(f"? Frontend responded with: {response.status_code}")
    except Exception as e:
        print(f"✗ Frontend not accessible: {e}")

def test_full_integration():
    """Test complete image+description workflow"""
    print("\n=== Testing Full Integration Workflow ===")
    
    base_url = "http://localhost:8000"
    
    # Test combined generation
    try:
        test_prompt = "mystical elf warrior with magical bow"
        payload = {
            "prompt": test_prompt,
            "character_name": "Lyra",
            "aspects": ["appearance", "personality", "background"],
            "style": "fantasy art"
        }
        
        response = requests.post(f"{base_url}/generate-image-with-description", 
                               json=payload)
        result = response.json()
        
        if result['success']:
            print(f"✓ Full integration successful: {result['message']}")
            if 'image_data' in result:
                print(f"  - Generated image: {result['image_data'][:50]}...")
            if 'description' in result:
                print(f"  - Generated description: {result['description'][:100]}...")
        else:
            print(f"✗ Full integration failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ Full integration error: {e}")

def check_dependencies():
    """Check all required dependencies"""
    print("\n=== Checking Dependencies ===")
    
    dependencies = {
        "Python": "python --version",
        "Node.js": "node --version",
        "Ollama": "ollama --version",
        "ComfyUI": "Check if accessible on port 8188",
        "Backend": "Check if running on port 8000",
        "Frontend": "Check if running on port 3000"
    }
    
    for name, command in dependencies.items():
        if name == "Python":
            try:
                import subprocess
                result = subprocess.run(["python", "--version"], capture_output=True, text=True)
                print(f"✓ {name}: {result.stdout.strip()}")
            except:
                print(f"✗ {name}: Not available")
        elif name == "Node.js":
            try:
                import subprocess
                result = subprocess.run(["node", "--version"], capture_output=True, text=True)
                print(f"✓ {name}: {result.stdout.strip()}")
            except:
                print(f"✗ {name}: Not available")
        elif name == "Ollama":
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                print(f"✓ {name}: Running with models")
            except:
                print(f"✗ {name}: Not running")
        elif name == "ComfyUI":
            try:
                response = requests.get("http://localhost:8188/system_stats", timeout=5)
                print(f"✓ {name}: Running")
            except:
                print(f"✗ {name}: Not accessible")
        elif name == "Backend":
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                print(f"✓ {name}: Running on port 8000")
            except:
                print(f"✗ {name}: Not accessible")
        elif name == "Frontend":
            try:
                response = requests.get("http://localhost:3000", timeout=5)
                print(f"✓ {name}: Running on port 3000")
            except:
                print(f"✗ {name}: Not accessible")

def generate_implementation_report():
    """Generate a report of current status and next steps"""
    print("\n=== Implementation Status Report ===")
    
    print("✅ COMPLETED:")
    print("  - Frontend setup (Next.js on port 3000)")
    print("  - Backend framework (FastAPI on port 8000)")
    print("  - Simple test backend with mock functionality")
    print("  - Ollama integration for text generation")
    print("  - Basic API endpoints and CORS setup")
    print("  - Environment configuration")
    
    print("\n⚠️  PARTIALLY COMPLETED:")
    print("  - Full backend integration (needs ComfyUI)")
    print("  - Image generation (test mode working, real mode pending)")
    print("  - Complete workflow integration")
    
    print("\n❌ NOT COMPLETED:")
    print("  - ComfyUI installation and running")
    print("  - Real image generation via ComfyUI")
    print("  - Complete frontend-backend integration")
    print("  - UI components and user interface")
    print("  - Error handling and user feedback")
    
    print("\n🎯 IMMEDIATE NEXT STEPS:")
    print("  1. Fix ComfyUI installation")
    print("  2. Start ComfyUI service on port 8188")
    print("  3. Test real image generation")
    print("  4. Connect frontend to backend APIs")
    print("  5. Build UI components")
    print("  6. Test complete end-to-end workflow")

def main():
    """Main test function"""
    print("Story Booker Comprehensive Integration Test")
    print("=" * 50)
    
    # Run all tests
    check_dependencies()
    test_current_backend()
    test_ai_services()
    test_frontend()
    test_full_integration()
    generate_implementation_report()
    
    print("\n" + "=" * 50)
    print("Test completed! Check the report above for status and next steps.")

if __name__ == "__main__":
    main()