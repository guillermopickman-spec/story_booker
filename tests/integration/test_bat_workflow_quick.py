#!/usr/bin/env python3
"""
Quick test for verifying the bat cartoon character workflow setup.
This test checks that the workflow is properly configured and the prompt is queued.
"""
import os
import sys
import json

# Setup environment
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
os.environ.setdefault("CHARACTER_WORKFLOW_NAME", "character_creator")

# Add modules to path
sys.path.insert(0, "modules")

from characters.image_gen.manager import ImageGenManager


def test_bat_workflow():
    """Test that the bat character workflow is properly configured."""
    print("Testing Bat Cartoon Character Workflow")
    
    try:
        # Initialize manager with the correct workflow
        image_manager = ImageGenManager(workflow_name="character_creator")
        
        # Check ComfyUI connection
        if not image_manager.check_comfyui_connection():
            print("FAIL: ComfyUI not accessible")
            return False
        
        print("OK: ComfyUI connected")
        
        # Create bat character prompt
        bat_prompt = """chibi bat character, big head, small body, cute cartoon style, 
        large expressive eyes, small wings, fluffy fur, dark purple and black color scheme,
        friendly expression, standing on two feet, character sheet, full body, white background,
        storybook watercolor style"""
        
        negative_prompt = """text, watermark, blurry, low quality"""
        
        # Get workflow and inspect it
        workflow = image_manager.get_workflow(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        if not workflow:
            print("FAIL: Could not get workflow")
            return False
        
        print(f"OK: Workflow loaded with {len(workflow)} nodes")
        
        # Check for positive prompt
        positive_nodes = [id for id, node in workflow.items() 
                         if node.get("class_type") == "CLIPTextEncode" 
                         and "positive" in str(node.get("inputs", {}).get("text", "")).lower()]
        
        if positive_nodes:
            print(f"OK: Positive prompt set at node {positive_nodes[0]}")
            actual_prompt = workflow[positive_nodes[0]]["inputs"]["text"]
            print(f"   Prompt: {actual_prompt[:80]}...")
        else:
            print("FAIL: Positive prompt not found")
            return False
        
        # Try to queue the prompt (but don't wait for completion)
        print("\nAttempting to queue prompt...")
        image_result = image_manager.generate_image(
            user_pos=bat_prompt,
            user_neg=negative_prompt
        )
        
        if image_result:
            prompt_id = image_result.get("prompt_id")
            print(f"OK: Prompt queued successfully")
            print(f"   Prompt ID: {prompt_id}")
            
            # Save workflow for inspection
            with open("tests/integration/bat_final_workflow.json", "w") as f:
                json.dump(workflow, f, indent=2)
            print("OK: Workflow saved to tests/integration/bat_final_workflow.json")
            
            return True
        else:
            print("FAIL: Could not queue prompt")
            return False
            
    except Exception as e:
        print(f"FAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bat_workflow()
    
    if success:
        print("\nSUCCESS: Bat cartoon character workflow test passed!")
        print("The image generation has been queued and should appear in ComfyUI.")
    else:
        print("\nFAILURE: Test failed")
    
    sys.exit(0 if success else 1)