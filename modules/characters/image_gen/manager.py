"""
Image Generation Manager

Manages the image generation workflow, including:
- Loading and validating ComfyUI client
- Retrieving and processing workflows
- Coordinating image generation
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional

from .client import ComfyClient
from .workflow_composer import WorkflowComposer

logger = logging.getLogger(__name__)


class ImageGenManager:
    """Manager for image generation tasks using ComfyUI."""
    
    def __init__(self, workflow_name: Optional[str] = None):
        """
        Initialize the ImageGenManager.
        
        Args:
            workflow_name: Optional specific workflow name to use.
        """
        # Load workflow path or name from environment with fallback
        workflow_path = os.getenv("CHARACTER_WORKFLOW_PATH")
        if workflow_path:
            # Use specific workflow path
            self.workflow_name = workflow_path
            self.composer = WorkflowComposer(template_path=workflow_path)
            logger.info(f"ImageGenManager initialized with workflow path: {workflow_path}")
        else:
            # Use workflow name
            self.workflow_name = workflow_name or os.getenv("CHARACTER_WORKFLOW_NAME")
            if not self.workflow_name:
                logger.warning("No workflow name specified. Defaulting to 'character_creator'")
                self.workflow_name = "character_creator"
            
            self.composer = WorkflowComposer()
            logger.info(f"ImageGenManager initialized with workflow: {self.workflow_name}")
        
        # Initialize ComfyUI client
        self.client = ComfyClient()
    
    def check_comfyui_connection(self) -> bool:
        """
        Check if ComfyUI is running and accessible.
        
        Returns:
            bool: True if ComfyUI is accessible, False otherwise
        """
        if self.client.check_comfyui_connection():
            logger.info("ComfyUI connection successful")
            return True
        else:
            logger.error("ComfyUI connection failed")
            return False
    
    def get_workflow(self, user_pos: str, user_neg: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the configured workflow with user prompts merged in.
        
        Args:
            user_pos: User's positive prompt
            user_neg: User's negative prompt (optional)
            
        Returns:
            Dict: The composed workflow ready to send to ComfyUI
            
        Raises:
            Exception: If workflow loading fails
        """
        try:
            logger.info(f"Getting workflow '{self.workflow_name}'")
            workflow = self.composer.compose(user_pos=user_pos, user_neg=user_neg)
            
            # Validate workflow structure
            if not workflow:
                raise ValueError("Generated workflow is empty")
            
            # Log key workflow parameters
            logger.debug(f"Workflow loaded with {len(workflow)} nodes")
            
            return workflow
            
        except FileNotFoundError as e:
            logger.error(f"Workflow file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid workflow JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            raise
    
    def generate_image(self, user_pos: str, user_neg: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an image using ComfyUI.
        
        Args:
            user_pos: User's positive prompt
            user_neg: User's negative prompt (optional)
            
        Returns:
            Optional[dict]: Response from ComfyUI including prompt ID and status
        """
        # Check connection first
        if not self.check_comfyui_connection():
            logger.error("Cannot generate image: ComfyUI is not accessible")
            return None
        
        try:
            # Get the workflow
            workflow = self.get_workflow(user_pos=user_pos, user_neg=user_neg)
            
            # Queue the prompt
            logger.info("Sending prompt to ComfyUI")
            response = self.client.queue_prompt(workflow)
            
            if response:
                prompt_id = response.get("prompt_id", "unknown")
                logger.info(f"Prompt queued successfully. Prompt ID: {prompt_id}")
                return response
            else:
                logger.error("Failed to queue prompt")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def get_status(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a queued prompt.
        
        Args:
            prompt_id: The prompt ID from the queue
            
        Returns:
            Optional[dict]: Status information from ComfyUI
        """
        try:
            endpoint = f"{self.client.base_url}/history/{prompt_id}"
            response = self.client.requests_client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting prompt status: {e}")
            return None