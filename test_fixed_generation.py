from modules.characters.image_gen.workflow_composer import WorkflowComposer
from modules.characters.image_gen.manager import ImageGenManager
import os

# Set the environment variable properly
os.environ["CHARACTER_WORKFLOW_PATH"] = "./workflows/character_creator_no_rmbg.json"

print("=== Testing Fixed Character Generation ===")

# Test 1: Verify clean workflow loads correctly
print("\n1. Testing clean workflow loading:")
composer = WorkflowComposer(template_path="./workflows/character_creator_no_rmbg.json")
template = composer._load_template()
has_rmbg = any(node.get('class_type') == 'RMBG' for node in template.values())
print(f"   Clean workflow loaded: {composer.loaded_template_path}")
print(f"   Has RMBG node: {has_rmbg}")

# Test 2: Test prompt composition
print("\n2. Testing prompt composition:")
workflow = composer.compose(
    user_pos="a cute baby fox with big eyes and fluffy tail",
    user_neg="text, watermark, blurry, low quality"
)
print(f"   Positive prompt: {workflow['6']['inputs']['text']}")
print(f"   Negative prompt: {workflow['7']['inputs']['text']}")

# Test 3: Test direct ComfyUI API call with clean workflow
print("\n3. Testing direct ComfyAPI call:")
import requests
import json

# Queue the prompt directly
endpoint = 'http://127.0.0.1:8188/prompt'
response = requests.post(endpoint, json={'prompt': workflow})

print(f"   Response status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    prompt_id = result.get('prompt_id')
    print(f"   Success! Prompt ID: {prompt_id}")
    print("   This should generate a cute baby fox without RMBG errors!")
else:
    print(f"   Error: {response.text}")

# Test 4: Test with fixed ImageGenManager
print("\n4. Testing with fixed ImageGenManager:")
try:
    # Create manager with clean workflow
    manager = ImageGenManager()
    manager.composer = WorkflowComposer(template_path="./workflows/character_creator_no_rmbg.json")
    
    print("   Checking ComfyUI connection...")
    connection_ok = manager.check_comfyui_connection()
    print(f"   Connection status: {connection_ok}")
    
    if connection_ok:
        print("   Generating cute baby fox...")
        response = manager.generate_image("a cute baby fox with big eyes and fluffy tail", "text, watermark, blurry, low quality")
        
        if response:
            prompt_id = response.get('prompt_id')
            print(f"   Success! Prompt ID: {prompt_id}")
            print("   Character generation started without RMBG issues!")
        else:
            print("   Failed to generate image")
    else:
        print("   ComfyUI not accessible")
        
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")