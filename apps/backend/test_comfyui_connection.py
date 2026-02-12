import requests
import json
import os
import sys

# Ensure the parent directory is in the path for module imports if needed
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMFYUI_URL = "http://127.0.0.1:8188"

print(f"Attempting to connect to ComfyUI at: {COMFYUI_URL}")

try:
    response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=10)
    response.raise_for_status() # Raise an exception for bad status codes
    
    print(f"Successfully connected to ComfyUI.")
    print(f"ComfyUI replied with status code: {response.status_code}")
    # print(f"System stats: {json.dumps(response.json(), indent=2)}") # Optional: print stats

except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: Could not connect to ComfyUI at {COMFYUI_URL}. Is it running?")
    print(e)
except requests.exceptions.Timeout:
    print(f"Timeout Error: Request to {COMFYUI_URL} timed out.")
except requests.exceptions.RequestException as e:
    print(f"An error occurred while requesting ComfyUI: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("Connection test finished.")