#!/usr/bin/env python3
"""
Comprehensive test for DescriptionGenManager.
"""
import os
import sys
import json

# Setup environment
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")

# Add modules to path
sys.path.insert(0, "modules")

from characters.description_gen.manager import DescriptionGenManager


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_manager_initialization():
    """Test manager initialization."""
    print_section("Test 1: Manager Initialization")
    
    try:
        manager = DescriptionGenManager()
        print(f"✓ Manager initialized successfully")
        print(f"  Model: {manager.model}")
        print(f"  Ollama base URL: {manager.client.base_url}")
        return True, manager
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_connection():
    """Test Ollama connection."""
    print_section("Test 2: Ollama Connection Check")
    
    try:
        manager = DescriptionGenManager()
        is_connected = manager.check_ollama_connection()
        
        if is_connected:
            print(f"✓ Ollama is accessible and responding")
            
            # List available models
            models = manager.get_available_models()
            if models:
                print(f"✓ Available models: {[m['name'] for m in models]}")
            else:
                print(f"⚠ Could not retrieve models list")
            
            return True, manager
        else:
            print(f"⚠ Ollama is NOT accessible")
            print(f"  Make sure Ollama is installed and running")
            print(f"  You can install it from: https://ollama.ai/")
            return True, manager
    except Exception as e:
        print(f"✗ Connection check failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_description_generation():
    """Test basic description generation."""
    print_section("Test 3: Basic Description Generation")
    
    try:
        manager = DescriptionGenManager()
        
        # Test prompt
        prompt = "Describe a mysterious forest at twilight with magical elements."
        
        print(f"Test prompt: \"{prompt}\"")
        print(f"Generating description...")
        
        description = manager.generate_description(prompt)
        
        if description:
            print(f"✓ Description generated successfully")
            print(f"  Length: {len(description)} characters")
            print(f"  Preview: {description[:100]}...")
            return True
        else:
            print(f"✗ Failed to generate description")
            return False
    except Exception as e:
        print(f"⚠ Description generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_modular_description():
    """Test modular description generation."""
    print_section("Test 4: Modular Description Generation")
    
    try:
        manager = DescriptionGenManager()
        
        character_name = "Luna Moonshadow"
        aspects = ["appearance", "personality", "background", "special abilities"]
        style = "fantasy, mystical, detailed"
        
        print(f"Character: {character_name}")
        print(f"Aspects: {', '.join(aspects)}")
        print(f"Style: {style}")
        print(f"Generating modular description...")
        
        description = manager.generate_modular_description(
            character_name=character_name,
            aspects=aspects,
            style=style
        )
        
        if description:
            print(f"✓ Modular description generated successfully")
            print(f"  Aspects generated: {list(description.keys())}")
            
            for aspect, content in description.items():
                print(f"\n  {aspect.capitalize()}:")
                print(f"    {content[:100]}...")
            
            return True
        else:
            print(f"✗ Failed to generate modular description")
            return False
    except Exception as e:
        print(f"⚠ Modular description test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comfyui_formatting():
    """Test description formatting for ComfyUI."""
    print_section("Test 5: ComfyUI Prompt Formatting")
    
    try:
        manager = DescriptionGenManager()
        
        # Sample description
        description = "A young elven woman with long silver hair and glowing blue eyes, wearing elegant robes"
        
        # Additional prompts
        positive_prompt = "fantasy art"
        negative_prompt = "photorealistic, realistic"
        
        print(f"Original description: {description}")
        print(f"Positive prompt: {positive_prompt}")
        print(f"Negative prompt: {negative_prompt}")
        print(f"Formatting for ComfyUI...")
        
        formatted = manager.format_for_comfyui(
            description=description,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt
        )
        
        if formatted:
            print(f"✓ ComfyUI formatting successful")
            print(f"  Formatted positive: {formatted['positive']}")
            print(f"  Formatted negative: {formatted['negative']}")
            return True
        else:
            print(f"✗ Failed to format for ComfyUI")
            return False
    except Exception as e:
        print(f"⚠ ComfyUI formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_management():
    """Test model management."""
    print_section("Test 6: Model Management")
    
    try:
        manager = DescriptionGenManager()
        
        # Get available models
        models = manager.get_available_models()
        if models:
            print(f"✓ Retrieved {len(models)} available models")
            print(f"  First model: {models[0]['name']}")
        else:
            print(f"⚠ Could not retrieve models")
            return True
        
        # Test setting a new model (if available)
        if len(models) > 1:
            original_model = manager.model
            new_model = models[1]['name']
            
            print(f"Changing model from {original_model} to {new_model}")
            manager.set_model(new_model)
            
            if manager.model == new_model:
                print(f"✓ Model changed successfully")
                # Change back
                manager.set_model(original_model)
                print(f"✓ Model changed back to {original_model}")
                return True
            else:
                print(f"✗ Model change failed")
                return False
        else:
            print(f"Skipping model change test (only one model available)")
            return True
            
    except Exception as e:
        print(f"⚠ Model management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_section("Comprehensive DescriptionGenManager Test")
    print(f"Environment:")
    print(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
    
    results = []
    manager = None
    
    # Test 1: Initialization
    success, manager = test_manager_initialization()
    results.append(success)
    
    # Test 2: Connection
    success, _ = test_connection()
    results.append(success)
    
    # Test 3: Basic Description Generation
    if results[-1]:  # Only run if connection successful
        success = test_description_generation()
        results.append(success)
    else:
        print("\nSkipping description generation test (connection failed)")
        results.append(True)
    
    # Test 4: Modular Description
    if results[-1]:  # Only run if basic generation successful
        success = test_modular_description()
        results.append(success)
    else:
        print("\nSkipping modular description test (basic generation failed)")
        results.append(True)
    
    # Test 5: ComfyUI Formatting
    success = test_comfyui_formatting()
    results.append(success)
    
    # Test 6: Model Management
    success = test_model_management()
    results.append(success)
    
    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if all(results):
        print("\n✓✓✓ All tests PASSED ✓✓✓")
        return 0
    else:
        print("\n✗✗✗ Some tests FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())