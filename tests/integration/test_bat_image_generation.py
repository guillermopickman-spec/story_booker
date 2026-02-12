#!/usr/bin/env python3
"""
Direct test for generating a bat cartoon character image using ComfyUI.
This test bypasses the AI description generation and directly tests image generation.
"""
import os
import sys
import json
import logging
import time

# Setup environment
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
os.environ.setdefault("CHARACTER_WORKFLOW_NAME", "character_creator")

# Add modules to path
sys.path.insert(0, "modules")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from characters.image_gen.manager import ImageGenManager


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_bat_image_generation():
    """Test generating a bat cartoon character image directly with ComfyUI."""
    print_section("Test: Bat Cartoon Character Image Generation")
    
    try:
        # Initialize manager with the correct workflow
        image_manager = ImageGenManager(workflow_name="character_creator")
        
        # Step 1: Check ComfyUI connection
        print("\n1. Checking ComfyUI connection...")
        comfyui_ok = image_manager.check_comfyui_connection()
        print(f"   ComfyUI: {'[OK] Connected' if comfyui_ok else '[FAIL] Not accessible'}")
        
        if not comfyui_ok:
            print("\n[FAIL] ComfyUI not accessible")
            return False
        
        # Step 2: Create bat character prompt
        print("\n2. Creating bat character prompt...")
        
        # Chibi bat character prompt
        bat_prompt = """chibi bat character, big head, small body, cute cartoon style, 
        large expressive eyes, small wings, fluffy fur, dark purple and black color scheme,
        friendly expression, standing on two feet, character sheet, full body, white background,
        storybook watercolor style, high quality, masterpiece, detailed, 8k"""
        
        negative_prompt = """text, watermark, blurry, low quality, distorted, 
        realistic, photograph, human, scary, threatening, bad anatomy"""
        
        print(f"   Positive: {bat_prompt}")
        print(f"   Negative: {negative_prompt}")
        
        # Step 3: Generate image with ComfyUI
        print("\n3. Generating image with ComfyUI...")
        image_result = image_manager.generate_image(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        if image_result:
            prompt_id = image_result.get("prompt_id")
            print("[OK] Image generation initiated")
            print(f"   Prompt ID: {prompt_id}")
            
            # Step 4: Monitor progress
            print("\n4. Monitoring image generation progress...")
            max_attempts = 30  # 5 minutes max waiting
            attempt = 0
            
            while attempt < max_attempts:
                status = image_manager.get_status(prompt_id)
                
                if status:
                    print(f"   Status: {status.get('status', 'Unknown')}")
                    
                    # Check if the prompt is complete
                    if status.get("status") == "success":
                        print("[OK] Image generation completed!")
                        
                        # Check for outputs
                        if 'outputs' in status:
                            outputs = status['outputs']
                            print(f"   Outputs: {list(outputs.keys())}")
                            
                            # Save the workflow for inspection
                            workflow = image_manager.get_workflow(
                                user_pos=bat_prompt,
                                user_neg=negative_prompt
                            )
                            with open("tests/integration/bat_image_workflow.json", "w") as f:
                                json.dump(workflow, f, indent=2)
                            print("[OK] Workflow saved to tests/integration/bat_image_workflow.json")
                            
                            return True
                        else:
                            print("[WARN] No outputs found in status")
                            return True
                    
                    elif status.get("status") in ["error", "failed"]:
                        print(f"[FAIL] Image generation failed: {status}")
                        return False
                
                attempt += 1
                print(f"   Waiting... ({attempt}/{max_attempts})")
                time.sleep(10)  # Wait 10 seconds between checks
            
            print("[WARN] Image generation timed out")
            return False
        else:
            print("[FAIL] Failed to initiate image generation")
            return False
            
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_inspection():
    """Test the workflow composition and inspect it."""
    print_section("Testing Workflow Inspection")
    
    try:
        image_manager = ImageGenManager(workflow_name="character_creator")
        
        # Create a bat character prompt
        bat_prompt = """chibi bat character, big head, small body, cute cartoon style, 
        large expressive eyes, small wings, fluffy fur, dark purple and black color scheme,
        friendly expression, standing on two feet, character sheet, full body, white background,
        storybook watercolor style"""
        
        negative_prompt = """text, watermark, blurry, low quality"""
        
        # Get the workflow
        workflow = image_manager.get_workflow(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        if not workflow:
            print("[FAIL] Failed to get workflow")
            return False
        
        print(f"[OK] Workflow retrieved with {len(workflow)} nodes")
        
        # Analyze workflow structure
        node_types = {}
        for node_id, node in workflow.items():
            node_type = node.get("class_type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_type == "CLIPTextEncode":
                if "text" in node.get("inputs", {}):
                    text = node["inputs"]["text"]
                    if "positive" in text.lower():
                        print(f"   Positive prompt node {node_id}: {text[:100]}...")
                    else:
                        print(f"   Negative prompt node {node_id}: {text[:100]}...")
        
        print("\n   Node types:")
        for node_type, count in node_types.items():
            print(f"     {node_type}: {count}")
        
        # Save workflow to file for inspection
        with open("tests/integration/bat_character_inspect_workflow.json", "w") as f:
            json.dump(workflow, f, indent=2)
        print("[OK] Workflow saved to tests/integration/bat_character_inspect_workflow.json")
        
        # Check for critical nodes
        critical_nodes = ["CheckpointLoaderSimple", "KSampler", "VAEDecode", "SaveImage"]
        missing_nodes = []
        
        for node_type in critical_nodes:
            if node_type not in node_types:
                missing_nodes.append(node_type)
        
        if missing_nodes:
            print(f"[WARN] Missing critical nodes: {missing_nodes}")
            return False
        else:
            print("[OK] All critical nodes found")
            return True
        
    except Exception as e:
        print(f"[FAIL] Workflow inspection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_section("Bat Cartoon Image Generation Tests")
    print(f"Environment:")
    print(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
    print(f"  CHARACTER_WORKFLOW_NAME: {os.getenv('CHARACTER_WORKFLOW_NAME')}")
    
    results = []
    
    # Test 1: Direct image generation
    success = test_bat_image_generation()
    results.append(("Direct Image Generation", success))
    
    # Test 2: Workflow inspection
    success = test_workflow_inspection()
    results.append(("Workflow Inspection", success))
    
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
        print("This might be due to ComfyUI not being available or workflow issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())