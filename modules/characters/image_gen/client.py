import requests
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class HostDiscovery:
    """Discovery class for host-based ComfyUI instances."""
    
    def discover(self) -> List[str]:
        """Discover ComfyUI instances on the local network."""
        return []  # Implement actual network discovery

class LocalhostDiscovery:
    """Discovery class for local ComfyUI instances."""
    
    def discover(self) -> List[str]:
        """Discover ComfyUI instances running on localhost."""
        return []  # Implement actual localhost discovery

DEFAULT_PORT = 8188
LOCALHOST = "127.0.0.1"
CONNECTION_TIMEOUT = 10

class ComfyClient:
    """
    ComfyUI client for interacting with the ComfyUI API.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the ComfyClient.
        
        Args:
            base_url: Optional base URL for ComfyUI. If not provided, uses environment variables.
        """
        # Load configuration from environment
        import os
        self.base_url = base_url or os.getenv("COMFYUI_HOST", "http://127.0.0.1") + ":" + os.getenv("COMFYUI_PORT", "8818")
        self.requests_client = requests.Session()
        self.requests_client.headers.update({"Content-Type": "application/json"})
        
        # Check connection on initialization
        if not self.check_comfyui_connection():
            logger.warning("ComfyUI connection check failed on initialization.")
    
    def check_comfyui_connection(self) -> bool:
        """
        Check if ComfyUI is running and accessible.
        
        Returns:
            bool: True if ComfyUI is accessible, False otherwise
        """
        try:
            # Test with a simple endpoint that exists
            response = self.requests_client.get(f"{self.base_url}/api/prompt", timeout=5)
            response.raise_for_status()
            
            # Check if we get the expected exec_info response
            if response.json().get("exec_info"):
                logger.info(f"ComfyUI connection successful. Queue remaining: {response.json().get('exec_info', {}).get('queue_remaining')}")
                return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ComfyUI connection failed: {e}")
            return False
    
    def queue_prompt(self, workflow: dict) -> Optional[dict]:
        """
        Queue a prompt with the given workflow.
        
        Args:
            workflow: The workflow configuration to send to ComfyUI
            
        Returns:
            Optional[dict]: Response from ComfyUI including prompt ID and status
        """
        try:
            endpoint = f"{self.base_url}/api/prompt"
            # ComfyUI expects the workflow under a "prompt" key
            payload = {"prompt": workflow}
            response = self.requests_client.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get("prompt_id") or result.get("id")
            logger.info(f"Prompt queued successfully. Prompt ID: {prompt_id}")
            # Include prompt_id in result
            if prompt_id:
                result["prompt_id"] = prompt_id
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error queuing prompt: {e}")
            if e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return None
    
    def get_history(self, prompt_id: str) -> Optional[dict]:
        """
        Get the history for a specific prompt.
        
        Args:
            prompt_id: The prompt ID to retrieve history for
            
        Returns:
            Optional[dict]: History information from ComfyUI
        """
        try:
            endpoint = f"{self.base_url}/api/history/{prompt_id}"
            response = self.requests_client.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting prompt history: {e}")
            return None
    
    def get_image(self, filename: str, subfolder: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve an image from ComfyUI.
        
        Args:
            filename: The filename of the image to retrieve
            subfolder: Optional subfolder where the image is located
            
        Returns:
            Optional[bytes]: The image content as bytes
        """
        try:
            endpoint = f"{self.base_url}/api/view"
            params = {"filename": filename}
            if subfolder:
                params["subfolder"] = subfolder
                
            response = self.requests_client.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Image retrieved successfully: {len(response.content)} bytes")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving image: {e}")
            return None