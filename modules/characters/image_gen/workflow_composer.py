import os
import json
import glob
import logging
import re
from dotenv import load_dotenv
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()
# Fallback to .env.example if .env doesn't exist
if not os.path.exists('.env'):
    load_dotenv('.env.example')


class WorkflowComposer:
    """Composes a ComfyUI workflow by loading from various sources."""

    def __init__(self, template_path: Optional[str] = None, workflow_dir: Optional[str] = None, workflow_name: Optional[str] = None):
        """
        Initialize the WorkflowComposer.
        
        Args:
            template_path: Specific template file path (if None, will search default locations).
            workflow_dir: Custom workflow directory to search for workflows (if None, uses defaults).
            workflow_name: Specific workflow file name to load (e.g., "character_creator.json").
                          If None, will search for preferred names or use first found.
        """
        self._template_path = template_path
        self.workflow_dir = workflow_dir or self._get_default_workflow_dir()
        self.workflow_name = workflow_name or os.getenv("CHARACTER_WORKFLOW_NAME")
        self._template: Optional[Dict[str, Any]] = None
        self._template_loaded = False

    @property
    def template_path(self) -> Optional[str]:
        """Get the template path. Does not auto-load template."""
        return self._template_path

    @property
    def loaded_template_path(self) -> Optional[str]:
        """Get the template path, loading template if not already loaded."""
        if not self._template_loaded:
            self._load_template()
        return self._template_path

    @template_path.setter
    def template_path(self, value: Optional[str]):
        """Set the template path."""
        self._template_path = value

    def _get_default_workflow_dir(self) -> str:
        """
        Get the default workflow directory with fallback locations.
        
        Returns:
            The directory to search for workflows.
        """
        # Common ComfyUI workflow directories across platforms
        workflow_dirs = [
            os.path.expanduser("~/.comfyui/workflows"),  # Linux/Unix ComfyUI (expanded)
            os.path.join(os.path.expanduser("~"), "ComfyUI", "web", "custom_nodes"),  # Windows ComfyUI default
            "./workflows",  # Local project workflows
            "../workflows",  # Parent directory workflows
        ]
        
        # Also check modules directory
        workflow_dirs.append(os.path.join(os.path.dirname(__file__), "workflows"))
        
        # Return the first existing directory
        for dir_path in workflow_dirs:
            expanded = os.path.expanduser(dir_path)
            if os.path.exists(expanded):
                return expanded
        
        # Default to current directory if none found
        return "."

    def _find_workflow_files(self) -> list:
        """
        Find all workflow JSON files in the workflow directory.
        
        Returns:
            List of workflow file paths.
        """
        if not os.path.exists(self.workflow_dir):
            return []
        
        # Search for JSON files in the workflow directory
        # Look for both .json files and compressed workflows
        json_files = glob.glob(os.path.join(self.workflow_dir, "*.json"))
        
        # If no JSON files found, look for ComfyUI compressed workflows
        if not json_files:
            compressed_files = glob.glob(os.path.join(self.workflow_dir, "*.jsonl"))
            if compressed_files:
                # Try to find the corresponding JSON file
                for cf in compressed_files:
                    base_name = os.path.splitext(cf)[0]
                    json_file = os.path.join(self.workflow_dir, base_name + ".json")
                    if os.path.exists(json_file):
                        json_files.append(json_file)
        
        return json_files

    def _load_template(self) -> Dict[str, Any]:
        """
        Load the workflow template from the best available source.
        
        Returns:
            The loaded workflow template.
            
        Raises:
            FileNotFoundError: If no workflow template can be found.
            json.JSONDecodeError: If the template file is invalid JSON.
        """
        if self._template is not None:
            return self._template
        
        # If specific template path is provided, use it
        if self._template_path:
            if not os.path.exists(self._template_path):
                raise FileNotFoundError(f"Template not found at: {self._template_path}")
            with open(self._template_path, 'r', encoding='utf-8') as f:
                self._template = json.load(f)
            # Don't set _template_path here as it's already set in __init__
            assert self._template is not None, "Template should be loaded by this point"
            return self._template
        
        # Search for workflows in default locations
        workflow_files = self._find_workflow_files()
        
        if not workflow_files:
            # No workflow files found - use programmatic fallback
            logger.warning("No workflow files found, using default workflow")
            self._template = self._create_default_workflow()
            # template_path remains None for default workflow
            assert self._template is not None, "Template should be loaded by this point"
            return self._template
        
        # Search for workflows in default locations
        workflow_files = self._find_workflow_files()
        
        if not workflow_files:
            # No workflow files found - use programmatic fallback
            logger.warning("No workflow files found, using default workflow")
            self._template = self._create_default_workflow()
            # template_path remains None for default workflow
            assert self._template is not None, "Template should be loaded by this point"
            return self._template
        
        # Initialize template_file to None
        template_file = None
        
        # Check if specific workflow_name is requested
        if self.workflow_name:
            # Remove .json extension if present
            workflow_basename = self.workflow_name
            if workflow_basename.endswith('.json'):
                workflow_basename = workflow_basename[:-5]
            
            # Look for file matching the workflow name
            for wf in workflow_files:
                if os.path.basename(wf) == workflow_basename:
                    template_file = wf
                    break
        
        # If no specific workflow_name found or not specified, use preferred names
        if not template_file:
            preferred_names = ["character_creator.json", "workflow_template.json", "default_workflow.json", "character_generator.json"]
            
            for name in preferred_names:
                for wf in workflow_files:
                    if os.path.basename(wf) == name:
                        template_file = wf
                        break
                if template_file:
                    break
        
        if not template_file and workflow_files:
            # If still no template_file found but we have workflow_files, use the first one
            template_file = workflow_files[0]
        
        if not template_file:
            raise FileNotFoundError("No workflow files found and no template file specified")
        
        logger.info(f"Loading workflow from: {template_file} (requested: {self.workflow_name})")
        with open(template_file, 'r', encoding='utf-8') as f:
            self._template = json.load(f)
        
        # Set the template_path when loading from file
        self._template_path = template_file
        self._template_loaded = True
        
        assert self._template is not None, "Template should be loaded by this point"
        return self._template

    def _create_default_workflow(self) -> Dict[str, Any]:
        """
        Create a simple default workflow if no template file is found.
        
        Returns:
            A minimal ComfyUI workflow template.
        """
        return {
            "1": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 0,
                    "steps": 20,
                    "cfg": 8,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "2": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.ckpt"
                }
            },
            "3": {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": "my_lora",
                    "strength_model": 1,
                    "strength_lora": 0.5
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "positive prompt here",
                    "clip": ["2", 0]
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "placeholder",
                    "clip": ["2", 0]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "placeholder",
                    "clip": ["2", 0]
                }
            }
        }

    def compose(self, user_pos: str, user_neg: Optional[str] = None) -> Dict[str, Any]:
        """
        Compose a workflow by loading a template and merging user inputs.
        
        Args:
            user_pos: User's positive prompt (character description).
            user_neg: User's negative prompt (optional).
            
        Returns:
            The composed workflow dictionary.
        """
        workflow = self._load_template()
        
        # Extract the style from the positive prompt if it contains the character sheet format
        # Look for style patterns in the prompt
        style_patterns = [
            r'\(character sheet:[^)]*\)',
            r'\(full body[^)]*\)',
            r'\([a-zA-Z\s]+style[^)]*\)',
            r'\([a-zA-Z\s]+[^)]*\)'
        ]
        
        base_prompt = user_pos
        extracted_styles = []
        
        for pattern in style_patterns:
            matches = re.findall(pattern, base_prompt, re.IGNORECASE)
            extracted_styles.extend(matches)
        
        # Remove style patterns from the base prompt to avoid duplication
        for pattern in style_patterns:
            base_prompt = re.sub(pattern, '', base_prompt, flags=re.IGNORECASE)
        
        base_prompt = base_prompt.strip()
        
        # Add quality tags from environment
        master_pos = os.getenv("POSITIVE_PROMPT", "")
        if master_pos:
            full_pos = f"{base_prompt}, {master_pos}".strip(", ")
        else:
            full_pos = base_prompt
        
        # Add extracted styles back to the prompt
        if extracted_styles:
            full_pos = f"{full_pos}, {' '.join(extracted_styles)}"
        
        # Identify nodes by class type (The standard way)
        text_nodes = [id for id, n in workflow.items() if n.get("class_type") == "CLIPTextEncode"]
        
        if text_nodes:
            # Find the positive prompt node - try common locations
            positive_node = None
            if "6" in text_nodes:  # This is the positive prompt in the current workflow
                positive_node = "6"
            elif "4" in text_nodes:  # Alternative location
                positive_node = "4"
            elif len(text_nodes) > 0:  # Fallback to first text node
                positive_node = text_nodes[0]
                
            if positive_node:
                workflow[positive_node]["inputs"]["text"] = full_pos
                logger.info(f"Set positive prompt at node {positive_node}: {full_pos[:100]}...")
        
        # Find the negative prompt node - try common locations
        negative_node = None
        if "7" in text_nodes:  # This is the negative prompt in the current workflow
            negative_node = "7"
        elif len(text_nodes) > 1:  # Fallback to second text node
            negative_node = text_nodes[1]
        
        if negative_node:
            if user_neg:  # Only use negative prompt if explicitly provided
                workflow[negative_node]["inputs"]["text"] = user_neg
                logger.info(f"Set negative prompt at node {negative_node}")
            else:
                # Always check for environment negative prompt first
                env_negative = os.getenv("NEGATIVE_PROMPT", "")
                if env_negative:
                    # Use environment negative prompt if available
                    workflow[negative_node]["inputs"]["text"] = env_negative
                    logger.info(f"Set environment negative prompt at node {negative_node}")
                else:
                    # Keep the default negative prompt from the workflow file
                    logger.info(f"Using default negative prompt at node {negative_node}")

        return workflow