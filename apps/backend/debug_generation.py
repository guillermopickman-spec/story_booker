#!/usr/bin/env python3
"""
Debug script to test image generation and saving
"""
import os
import sys
import requests
import json
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.characters.image_gen.manager import ImageGenManager

def test_generation():
    # Initialize the image manager
    image_manager = ImageGenManager()
    
    print(f"ComfyUI base URL: {image_manager.client.base_url}")
    print(f"ComfyUI connection: {image_manager.check_comfyui_connection()}")
    
    # Test with a simple prompt
    prompt = "a cute baby octopus with big curious eyes"
    print(f"Generating image with prompt: {prompt}")
    
    # Generate the image
    response = image_manager.generate_image(user_pos=prompt)
    
    if response:
        prompt_id = response.get("prompt_id")
        print(f"Prompt queued successfully. ID: {prompt_id}")
        
        # Wait for completion
        if prompt_id:
            print("Waiting for image generation...")
            
            max_attempts = 60  # 1 minute max
            attempt = 0
            
            while attempt < max_attempts:
                # Check if the prompt is complete
                endpoint = f"{image_manager.client.base_url}/history/{prompt_id}"
                try:
                    history_response = requests.get(endpoint, timeout=5)
                    
                    if history_response.status_code == 200:
                        history = history_response.json()
                        if prompt_id in history and "outputs" in history[prompt_id]:
                            print("Image generation complete!")
                            
                            # Find the image output
                            for node_id, node_output in history[prompt_id]["outputs"].items():
                                if "images" in node_output:
                                    image_info = node_output["images"][0]
                                    filename = image_info["filename"]
                                    subfolder = image_info.get("subfolder", "")
                                    
                                    print(f"Found image: {filename} in {subfolder}")
                                    
                                    # Get the image
                                    image_endpoint = f"{image_manager.client.base_url}/view"
                                    params = {"filename": filename, "subfolder": subfolder}
                                    img_response = requests.get(image_endpoint, params=params)
                                    
                                    if img_response.status_code == 200:
                                        print(f"Image retrieved successfully: {len(img_response.content)} bytes")
                                        
                                        # Save the image
                                        from pathlib import Path
                                        import datetime
                
                                        outputs_dir = Path(__file__).parent.parent / "outputs" / "images"
                                        outputs_dir.mkdir(parents=True, exist_ok=True)
                                        
                                        timestamp = int(time.time())
                                        original_name = Path(filename).stem
                                        file_ext = Path(filename).suffix
                                        safe_filename = f"{original_name}_{timestamp}{file_ext}"
                                        save_path = outputs_dir / safe_filename
                                        
                                        with open(save_path, "wb") as f:
                                            f.write(img_response.content)
                                        
                                        print(f"Image saved to: {save_path}")
                                        return True
                                    else:
                                        print(f"Failed to get image: {img_response.status_code}")
                                        return False
                            
                            print("No images found in outputs")
                            return False
                        else:
                            print(f"Prompt not complete yet. Status: {history}")
                    else:
                        print(f"History request failed: {history_response.status_code}")
                except Exception as e:
                    print(f"Error checking history: {e}")
                
                # Wait before next attempt
                time.sleep(2)
                attempt += 1
                print(f"Waiting... attempt {attempt}/{max_attempts}")
            
            print("Image generation timed out")
            return False
    else:
        print("Failed to queue prompt")
        return False

if __name__ == "__main__":
    test_generation()