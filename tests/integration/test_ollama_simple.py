#!/usr/bin/env python3
"""
Simple test for Ollama description generation.
Tests basic Ollama connection and prompt generation without complex workflows.
"""
import os
import sys
import json

# Setup environment
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")

# Add modules to path
sys.path.insert(0, "modules")

from characters.description_gen.client import OllamaClient


def test_ollama_connection():
    """Test basic Ollama connection."""
    print("Testing Ollama Connection...")
    
    try:
        client = OllamaClient()
        connected = client.check_connection()
        
        if connected:
            print("[OK] Ollama connection successful")
            return True
        else:
            print("[FAIL] Ollama connection failed")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_basic_description():
    """Test basic description generation with Ollama."""
    print("\nTesting Basic Description Generation...")
    
    try:
        client = OllamaClient()
        
        # Simple prompt for bat character
        prompt = "Generate a detailed description of a cute cartoon bat character with chibi style. Include appearance, personality, and special features."
        
        print(f"Prompt: {prompt}")
        
        # Generate description
        response = client.generate(prompt)
        
        if response and "response" in response:
            description = response["response"].strip()
            print(f"\nGenerated Description:")
            print("=" * 50)
            print(description)
            print("=" * 50)
            print("[OK] Description generated successfully")
            return True
        else:
            print("[FAIL] No response received")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_character_description():
    """Test character-specific description generation."""
    print("\nTesting Character Description Generation...")
    
    try:
        client = OllamaClient()
        
        # Character-specific prompt
        prompt = """Create a detailed character description for "Barnaby the Bat" in chibi style.
        
        Include:
        - Physical appearance (size, features, colors)
        - Personality traits
        - Unique characteristics
        - Overall aesthetic
        
        Return the description in a vivid, creative style suitable for image generation."""
        
        print(f"Prompt: {prompt[:100]}...")
        
        # Generate description
        response = client.generate(prompt, temperature=0.7)
        
        if response and "response" in response:
            description = response["response"].strip()
            print(f"\nGenerated Character Description:")
            print("=" * 60)
            print(description)
            print("=" * 60)
            print("[OK] Character description generated successfully")
            
            # Save to file for review
            with open("tests/integration/barnaby_description.txt", "w") as f:
                f.write(description)
            print("[OK] Description saved to tests/integration/barnaby_description.txt")
            
            return True
        else:
            print("[FAIL] No response received")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_style_aware_description():
    """Test description generation with style awareness."""
    print("\nTesting Style-Aware Description Generation...")
    
    try:
        client = OllamaClient()
        
        # Style-specific prompt
        prompt = """Generate a character description for "Barnaby the Bat" in chibi/cartoon style.
        
        Style requirements:
        - Big head, small body proportions
        - Cute, friendly appearance
        - Bright, appealing colors
        - Simple but expressive features
        
        Include details about:
        - Fur texture and color
        - Eye expression
        - Wing appearance
        - Overall pose and stance
        
        Make the description vivid and specific for image generation."""
        
        print(f"Prompt: {prompt[:100]}...")
        
        # Generate description
        response = client.generate(prompt, temperature=0.7)
        
        if response and "response" in response:
            description = response["response"].strip()
            print(f"\nGenerated Style-Aware Description:")
            print("=" * 60)
            print(description)
            print("=" * 60)
            print("[OK] Style-aware description generated successfully")
            
            # Save to file for review
            with open("tests/integration/barnaby_style_description.txt", "w") as f:
                f.write(description)
            print("[OK] Description saved to tests/integration/barnaby_style_description.txt")
            
            return True
        else:
            print("[FAIL] No response received")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def main():
    """Run all tests."""
    print("Ollama Simple Description Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Connection
    success = test_ollama_connection()
    results.append(("Connection Test", success))
    
    # Test 2: Basic description
    success = test_basic_description()
    results.append(("Basic Description", success))
    
    # Test 3: Character description
    success = test_character_description()
    results.append(("Character Description", success))
    
    # Test 4: Style-aware description
    success = test_style_aware_description()
    results.append(("Style-Aware Description", success))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    if all(success for _, success in results):
        print("\n✓ All tests PASSED!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())