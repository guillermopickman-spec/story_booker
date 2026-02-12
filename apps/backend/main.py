import requests
import base64
import os
import time
from pathlib import Path

from modules.characters.image_gen.manager import ImageGenManager

async def get_generated_image(prompt_id: str):
    """
    Retrieves the generated image from ComfyUI, saves it locally, and returns its base64 representation.
    """
    image_manager = ImageGenManager() # Assuming ImageGenManager is accessible here
    
    try:
        # Check ComfyUI connection (optional, but good practice)
        if not image_manager.check_comfyui_connection():
            print("ComfyUI server is not available when trying to get image.")
            return None

        # Get history to find the image details
        history_endpoint = f"{image_manager.client.base_url}/history/{prompt_id}"
        try:
            history_response = image_manager.client.requests_client.get(history_endpoint, timeout=10) # Increased timeout for history call
            history_response.raise_for_status() # Raise an exception for bad status codes
        except requests.exceptions.RequestException as e:
            print(f"Error fetching history for prompt {prompt_id}: {e}")
            return None

        history = history_response.json()
        
        if prompt_id in history and "outputs" in history[prompt_id]:
            prompt_data = history[prompt_id]
            if "images" in prompt_data and prompt_data["images"]:
                # Get the first image details
                image_info = prompt_data["images"][0]
                filename = image_info["filename"]
                subfolder = image_info.get("subfolder", "")
                
                print(f"Image generation complete for prompt {prompt_id}. Found filename: '{filename}' (subfolder: '{subfolder}')")

                # Attempt to retrieve the image from ComfyUI's /view endpoint
                image_endpoint = f"{image_manager.client.base_url}/view"
                params = {"filename": filename, "subfolder": subfolder}
                try:
                    print(f"Attempting to retrieve image from: {image_endpoint} with params: {params}")
                    img_response = image_manager.client.requests_client.get(image_endpoint, params=params, timeout=30) # Increased timeout for image retrieval
                    img_response.raise_for_status() # Raise an exception for bad status codes

                    print(f"Image retrieved successfully from ComfyUI: {len(img_response.content)} bytes")

                    # Convert to base64 for API response
                    import base64
                    base64_image = base64.b64encode(img_response.content).decode('utf-8')
                    
                    # --- Image Saving Logic ---
                    import os
                    import time
                    from pathlib import Path
                    
                    # Define the save directory relative to the backend script's location
                    # Assuming main.py is in story_booker/apps/backend
                    backend_dir = Path(__file__).parent.parent
                    outputs_dir = backend_dir.parent.parent / "outputs" / "images"
                    outputs_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate timestamped filename
                    timestamp = int(time.time())
                    original_name = Path(filename).stem
                    file_ext = Path(filename).suffix
                    safe_filename = f"{original_name}_{timestamp}{file_ext}"
                    save_path = outputs_dir / safe_filename
                    
                    # Save the image
                    try:
                        with open(save_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"Image successfully saved to: {save_path}")
                    except IOError as e:
                        print(f"IOError while saving image to {save_path}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred while saving image to {save_path}: {e}")
                    # --- End Image Saving Logic ---
                    
                    return base64_image
                except requests.exceptions.Timeout:
                    print("Timeout when trying to retrieve image from ComfyUI.")
                    return None
                except requests.exceptions.RequestException as e:
                    print(f"An error occurred while retrieving image from ComfyUI: {e}")
                    return None
            else:
                print(f"No 'images' key found in outputs for prompt {prompt_id}.")
                return None
        else:
            print(f"Prompt {prompt_id} not found in history or has no outputs.")
            return None
            
    except Exception as e:
        print(f"An unexpected error occurred in get_generated_image: {e}")
        return None