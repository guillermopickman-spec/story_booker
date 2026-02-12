#!/usr/bin/env python3
"""
Test script to verify image saving functionality
"""
import os
import sys
import requests
import base64
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.characters.image_gen.manager import ImageGenManager

def test_image_saving():
    # Initialize the image manager
    image_manager = ImageGenManager()
    
    # Check if ComfyUI is available
    if not image_manager.check_comfyui_connection():
        print("ComfyUI is not available")
        return
    
    # Generate a simple test image
    print("Generating test image...")
    response = image_manager.generate_image(
        user_pos="a cute baby octopus with big curious eyes",
        user_neg="blurry, low quality"
    )
    
    if response is None:
        print("Failed to generate image")
        return
    
    prompt_id = response.get("prompt_id")
    print(f"Generated image with prompt ID: {prompt_id}")
    
    # Wait for completion and save image
    if prompt_id:
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            # Check if the prompt is complete
            endpoint = f"{image_manager.client.base_url}/history/{prompt_id}"
            history_response = image_manager.client.requests_client.get(endpoint)
            
            if history_response.status_code == 200:
                history = history_response.json()
                if prompt_id in history and "outputs" in history[prompt_id]:
                    # Image generation is complete
                    print("Image generation complete, saving...")
                    
                    # Find the image output
                    for node_id, node_output in history[prompt_id]["outputs"].items():
                        if "images" in node_output:
                            # Get the first image
                            image_info = node_output["images"][0]
                            filename = image_info["filename"]
                            subfolder = image_info.get("subfolder", "")
                            
                            # Get the image
                            image_endpoint = f"{image_manager.client.base_url}/view"
                            params = {"filename": filename, "subfolder": subfolder}
                            img_response = image_manager.client.requests_client.get(image_endpoint, params=params)
                            
                            if img_response.status_code == 200:
                                # Save image to outputs directory
                                import time
                                
                                # Create outputs directory if it doesn't exist
                                outputs_dir = Path(__file__).parent.parent / "outputs" / "images"
                                outputs_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Generate timestamped filename
                                timestamp = int(time.time())
                                original_name = Path(filename).stem
                                file_ext = Path(filename).suffix
                                safe_filename = f"{original_name}_{timestamp}{file_ext}"
                                save_path = outputs_dir / safe_filename
                                
                                # Save the image
                                with open(save_path, "wb") as f:
                                    f.write(img_response.content)
                                
                                print(f"Image saved to: {save_path}")
                                return
                            else:
                                print(f"Failed to get image: {img_response.status_code}")
                                return
            
            # Wait before next attempt
            import time
            time.sleep(1)
            attempt += 1
            print(f"Waiting... attempt {attempt}/{max_attempts}")
        
        print("Image generation timed out")
    else:
        print("Failed to get prompt ID")

if __name__ == "__main__":
    test_image_saving()