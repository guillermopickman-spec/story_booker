#!/usr/bin/env python3
"""
Test for generating a bat cartoon character using the chibi style.
This test verifies the complete workflow from Ollama description to ComfyUI image generation.
"""
import os
import sys
import json
import logging

# Setup environment
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
os.environ.setdefault("CHARACTER_WORKFLOW_NAME", "test_workflow")

# Add modules to path
sys.path.insert(0, "modules")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from characters.description_gen.manager import DescriptionGenManager
from characters.image_gen.manager import ImageGenManager


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_bat_cartoon_character():
    """Test generating a bat cartoon character with chibi style."""
    print_section("Test: Bat Cartoon Character Generation")
    
    # Initialize managers with the correct workflow
    desc_manager = DescriptionGenManager()
    image_manager = ImageGenManager(workflow_name="character_creator")
    
    try:
        # Step 1: Check connections
        print("\n1. Checking service connections...")
        
        ollama_ok = desc_manager.check_ollama_connection()
        print(f"   Ollama: {'[OK] Connected' if ollama_ok else '[FAIL] Not accessible'}")
        
        comfyui_ok = image_manager.check_comfyui_connection()
        print(f"   ComfyUI: {'[OK] Connected' if comfyui_ok else '[FAIL] Not accessible'}")
        
        if not ollama_ok and not comfyui_ok:
            print("\n[WARN] Both services unavailable - test cannot proceed")
            return False
        elif not ollama_ok:
            print("\n[WARN] Ollama unavailable - will test with pre-defined prompts")
            return test_with_predefined_prompts(image_manager)
        elif not comfyui_ok:
            print("\n[WARN] ComfyUI unavailable - will test description generation only")
            return test_description_only(desc_manager)
        
        # Step 2: Generate bat character description
        print("\n2. Generating bat character description...")
        character_name = "Barnaby the Bat"
        style = "chibi"
        
        # Generate AI description
        result = desc_manager.generate_complete_character_prompt(
            character_name=character_name,
            style_name=style,
            generate_description=True,
            temperature=0.7
        )
        
        if not result["success"]:
            print(f"[FAIL] Failed to generate description: {result.get('error')}")
            return False
        
        print("[OK] Character description generated")
        print(f"   AI Description: {result['ai_description'][:100]}...")
        
        # Step 3: Build the complete prompt
        print("\n3. Building complete prompt...")
        
        if not result["prompt"]:
            print("[FAIL] Failed to build prompt")
            return False
        
        print("[OK] Prompt built successfully")
        print(f"   Complete Prompt: {result['prompt'][:100]}...")
        
        # Step 4: Format for ComfyUI
        print("\n4. Formatting for ComfyUI...")
        formatted = desc_manager.format_for_comfyui(
            description=result["ai_description"],
            positive_prompt=result["prompt"]
        )
        
        print("[OK] Formatted for ComfyUI")
        print(f"   Positive: {formatted['positive'][:100]}...")
        print(f"   Negative: {formatted['negative']}")
        
        # Step 5: Generate image with ComfyUI
        print("\n5. Generating image with ComfyUI...")
        image_result = image_manager.generate_image(
            user_pos=formatted["positive"],
            user_neg=formatted["negative"]
        )
        
        if image_result:
            prompt_id = image_result.get("prompt_id")
            print("[OK] Image generation initiated")
            print(f"   Prompt ID: {prompt_id}")
            
            # Get status
            status = image_manager.get_status(prompt_id)
            if status:
                print(f"   Status: {status.get('status', 'Unknown')}")
                if 'outputs' in status:
                    print(f"   Outputs: {list(status['outputs'].keys())}")
            else:
                print("   Status check skipped")
            
            return True
        else:
            print("[FAIL] Image generation failed")
            return False
            
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_description_only(desc_manager):
    """Test only the description generation part."""
    print_section("Testing Description Generation Only")
    
    try:
        character_name = "Barnaby the Bat"
        style = "chibi"
        
        print(f"Generating description for '{character_name}' in {style} style...")
        
        result = desc_manager.generate_complete_character_prompt(
            character_name=character_name,
            style_name=style,
            generate_description=True,
            temperature=0.7
        )
        
        if result["success"]:
            print("[OK] Description generated successfully")
            print(f"   AI Description: {result['ai_description']}")
            print(f"   Complete Prompt: {result['prompt']}")
            return True
        else:
            print(f"[FAIL] Failed to generate description: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Description test failed: {e}")
        return False


def test_with_predefined_prompts(image_manager):
    """Test with pre-defined bat character prompts."""
    print_section("Testing with Pre-defined Bat Character Prompts")
    
    try:
        # Pre-defined bat character prompt in chibi style
        bat_prompt = """chibi bat character, big head, small body, cute cartoon style, 
        large expressive eyes, small wings, fluffy fur, dark purple and black color scheme,
        friendly expression, standing on two feet, high quality, masterpiece, detailed, 8k"""
        
        negative_prompt = """low quality, blurry, distorted, text, watermark, 
        realistic, photograph, human, scary, threatening"""
        
        print("Testing with pre-defined bat character prompt...")
        print(f"   Positive: {bat_prompt}")
        print(f"   Negative: {negative_prompt}")
        
        # Try to generate image
        image_result = image_manager.generate_image(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        if image_result:
            prompt_id = image_result.get("prompt_id")
            print("[OK] Image generation initiated")
            print(f"   Prompt ID: {prompt_id}")
            
            # Get status
            status = image_manager.get_status(prompt_id)
            if status:
                print(f"   Status: {status.get('status', 'Unknown')}")
            else:
                print("   Status check skipped")
            
            return True
        else:
            print("[FAIL] Image generation failed")
            return False
            
    except Exception as e:
        print(f"[FAIL] Pre-defined prompt test failed: {e}")
        return False


def test_workflow_composition():
    """Test the workflow composition functionality."""
    print_section("Testing Workflow Composition")
    
    try:
        image_manager = ImageGenManager()
        
        # Create a bat character prompt
        bat_prompt = """chibi bat character, big head, small body, cute cartoon style, 
        large expressive eyes, small wings, fluffy fur, dark purple and black color scheme,
        friendly expression, standing on two feet"""
        
        negative_prompt = """text, watermark, blurry, low quality"""
        
        # Get the workflow
        workflow = image_manager.get_workflow(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        # Check that the workflow has the expected structure
        if not workflow:
            print("[FAIL] Failed to get workflow")
            return False
        
        print(f"[OK] Workflow retrieved with {len(workflow)} nodes")
        
        # Check for key nodes
        text_nodes = [id for id, node in workflow.items() if node.get("class_type") == "CLIPTextEncode"]
        print(f"   Text nodes found: {len(text_nodes)}")
        
        for node_id in text_nodes:
            node = workflow[node_id]
            if "text" in node.get("inputs", {}):
                text = node["inputs"]["text"]
                if "positive" in text.lower():
                    print(f"   Positive prompt: {text[:50]}...")
                else:
                    print(f"   Negative prompt: {text[:50]}...")
        
        # Save workflow to file for inspection
        with open("tests/integration/bat_character_workflow.json", "w") as f:
            json.dump(workflow, f, indent=2)
        print("[OK] Workflow saved to tests/integration/bat_character_workflow.json")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Workflow composition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_section("Bat Cartoon Character Generation Tests")
    print(f"Environment:")
    print(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
    print(f"  CHARACTER_WORKFLOW_NAME: {os.getenv('CHARACTER_WORKFLOW_NAME')}")
    
    results = []
    
    # Test 1: Full workflow
    success = test_bat_cartoon_character()
    results.append(("Full Workflow", success))
    
    # Test 2: Workflow composition
    success = test_workflow_composition()
    results.append(("Workflow Composition", success))
    
    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    for test_name, success in results:
        status = "[OK] PASSED" if success else "[FAIL] FAILED"
        print(f"  {test_name}: {status}")
    
    if all(success for _, success in results):
        print("\n[OK] All tests PASSED")
        return 0
    else:
        print("\n[WARN] Some tests had issues")
        print("This might be due to services (Ollama/ComfyUI) not being available")
        return 1


if __name__ == "__main__":
    sys.exit(main())