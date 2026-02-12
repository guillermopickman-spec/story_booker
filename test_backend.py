#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.characters.image_gen.manager import ImageGenManager

# Set the environment variable
os.environ['CHARACTER_WORKFLOW_PATH'] = './workflows/character_creator_fixed.json'

# Initialize the manager
manager = ImageGenManager()

print("Testing backend configuration:")
print(f"Workflow name: {manager.workflow_name}")
print(f"Template path: {manager.composer.template_path}")
print(f"ComfyUI connection: {manager.check_comfyui_connection()}")

# Test workflow composition
workflow = manager.get_workflow("a brave warrior with a sword", "text, watermark")
print(f"Workflow keys: {list(workflow.keys())}")

# Test image generation
response = manager.generate_image("a brave warrior with a sword", "text, watermark")
print(f"Generate response: {response}")