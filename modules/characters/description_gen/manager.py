import os
import json
import logging
import re
from typing import Dict, Any, Optional, List

from .client import OllamaClient

logger = logging.getLogger(__name__)


class DescriptionGenManager:
    """Manager for description generation tasks using Ollama."""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the DescriptionGenManager.
        
        Args:
            model: Optional specific model to use.
        """
        # Load model from environment with fallback
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        if not self.model:
            logger.warning("No model specified. Defaulting to 'llama3.1:8b'")
            self.model = "llama3.1:8b"
        
        logger.info(f"DescriptionGenManager initialized with model: {self.model}")
        
        # Initialize Ollama client
        self.client = OllamaClient(model=self.model)
    
    def check_ollama_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            bool: True if Ollama is accessible, False otherwise
        """
        if self.client.check_connection():
            logger.info("Ollama connection successful")
            return True
        else:
            logger.error("Ollama connection failed")
            return False
    
    def _clean_json_response(self, response_text: str) -> Optional[str]:
        """
        Clean and extract JSON from response text.
        
        Args:
            response_text: The raw response from Ollama
            
        Returns:
            Optional[str]: Cleaned JSON string or None if parsing fails
        """
        response_text = response_text.strip()
        
        # Case 1: Direct JSON
        if response_text.startswith('{') and response_text.endswith('}'):
            try:
                json.loads(response_text)
                return response_text
            except json.JSONDecodeError:
                pass
        
        # Case 2: Markdown JSON (```json ... ```)
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            json_lines = []
            in_json_block = False
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_json_block:
                        break  # End of JSON block
                    in_json_block = True
                    continue
                elif in_json_block:
                    json_lines.append(line)
            
            if json_lines:
                json_text = '\n'.join(json_lines).strip()
                try:
                    json.loads(json_text)
                    return json_text
                except json.JSONDecodeError:
                    pass
        
        # Case 3: JSON in regular text (look for {...})
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group())
                return json_match.group()
            except json.JSONDecodeError:
                pass
        
        # Case 4: Try to extract JSON-like structure from text
        # Look for key-value pairs that form a JSON object
        key_pattern = r'"([^"]+)"\s*:'
        keys = re.findall(key_pattern, response_text)
        
        if len(keys) >= 2:  # At least 2 keys to be useful
            # Try to build a JSON object from the text
            json_obj = {}
            current_key = None
            
            for line in response_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Look for key
                key_match = re.match(r'"([^"]+)"\s*:', line)
                if key_match:
                    current_key = key_match.group(1)
                    # Get the rest of the line as value
                    value_part = line[len(key_match.group(0)):].strip()
                    if value_part.startswith('"'):
                        # String value
                        json_obj[current_key] = value_part[1:-1] if value_part.endswith(',') else value_part[1:-1]
                    elif value_part.startswith('['):
                        # Array value
                        try:
                            json_obj[current_key] = json.loads(value_part)
                        except json.JSONDecodeError:
                            json_obj[current_key] = value_part
                    elif value_part.startswith('{'):
                        # Object value
                        try:
                            json_obj[current_key] = json.loads(value_part)
                        except json.JSONDecodeError:
                            json_obj[current_key] = value_part
                    else:
                        # Other value
                        json_obj[current_key] = value_part
                
                elif current_key and line.startswith('"') and ':' not in line:
                    # Continuation of value
                    json_obj[current_key] += ' ' + line.strip('"')
            
            if json_obj:
                try:
                    json_str = json.dumps(json_obj)
                    json.loads(json_str)  # Validate it's valid JSON
                    return json_str
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return None
    
    def generate_description(self, prompt: str, system: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Generate a description using Ollama.
        
        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt
            **kwargs: Additional parameters for the model
            
        Returns:
            Optional[str]: Generated description or None if error
        """
        # Check connection first
        if not self.check_ollama_connection():
            logger.error("Cannot generate description: Ollama is not accessible")
            return None
        
        try:
            # Generate the description
            response = self.client.generate(prompt, system=system, **kwargs)
            
            if response and "response" in response:
                description = response["response"].strip()
                logger.info(f"Description generated successfully ({len(description)} chars)")
                return description
            else:
                logger.error("Invalid response from Ollama")
                return None
                
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return None
    
    def generate_modular_description(self, character_name: str, aspects: Optional[List[str]] = None, 
                                   style: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Generate a modular character description with multiple aspects.
        
        Args:
            character_name: Name of the character
            aspects: List of aspects to describe (appearance, personality, background, etc.)
            style: Optional style guidance
            
        Returns:
            Optional[dict]: Dictionary with description aspects or None if error
        """
        # Default aspects if not specified
        default_aspects = ["appearance", "personality", "background", "mannerisms"]
        aspects = aspects or default_aspects
        
        # Create system prompt
        system_prompt = """You are a creative writer specializing in character descriptions.
        Generate detailed, vivid descriptions for character aspects.
        Focus on creating evocative, original content that would be useful for image generation.
        Return your response as a JSON object with keys exactly matching the requested aspect names.
        Do not include any introductory text or explanations - only the JSON object."""
        
        # Build the main prompt
        prompt = f"Generate a detailed character description for '{character_name}'. "
        
        if style:
            prompt += f"The style should be: {style}. "
            
        prompt += f"Please provide descriptions for the following aspects: {', '.join(aspects)}. "
        prompt += "Return ONLY a JSON object with keys exactly matching the aspect names. No other text."
        
        # Generate the description
        response = self.client.generate(prompt, system=system_prompt, temperature=0.7)
        
        if response and "response" in response:
            try:
                # Parse the JSON response with enhanced cleaning
                response_text = response["response"].strip()
                cleaned_json = self._clean_json_response(response_text)
                
                if cleaned_json:
                    description_json = json.loads(cleaned_json)
                    logger.info(f"Modular description generated with aspects: {list(description_json.keys())}")
                    return description_json
                else:
                    logger.error("Could not extract valid JSON from response")
                    logger.debug(f"Raw response: {response_text}")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from Ollama: {e}")
                logger.error(f"Response text: {response['response']}")
                return None
        else:
            logger.error("Invalid response from Ollama")
            return None
    
    def format_for_comfyui(self, description: str, positive_prompt: Optional[str] = None, 
                          negative_prompt: Optional[str] = None) -> Dict[str, str]:
        """
        Format a description for ComfyUI prompt generation.
        
        Args:
            description: The character description
            positive_prompt: Additional positive prompt elements
            negative_prompt: Negative prompt elements
            
        Returns:
            dict: Dictionary with formatted prompts for ComfyUI
        """
        # Basic formatting - can be enhanced based on workflow requirements
        base_positive = f"{description}, high quality, masterpiece, detailed, 8k"
        
        if positive_prompt:
            base_positive = f"{positive_prompt}, {base_positive}"
        
        formatted = {
            "positive": base_positive,
            "negative": negative_prompt or "low quality, blurry, distorted, text, watermark"
        }
        
        logger.info(f"Formatted prompts for ComfyUI - Positive: {base_positive[:60]}...")
        return formatted
    
    def get_available_models(self) -> Optional[List[str]]:
        """
        Get list of available models from Ollama.
        
        Returns:
            Optional[List[str]]: List of model names or None if error
        """
        return self.client.list_models()
    
    def set_model(self, model: str) -> None:
        """
        Change the model used for generation.
        
        Args:
            model: New model name
        """
        self.client.set_model(model)
        logger.info(f"Changed model to: {model}")
    
    def generate_complete_character_prompt(self,
                                        character_name: str,
                                        style_name: str = "anime",
                                        generate_description: bool = True,
                                        custom_ai_description: Optional[str] = None,
                                        temperature: float = 0.7,
                                        custom_style: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete character prompt using the prompt-gen module.
        
        Args:
            character_name: Name of the character
            style_name: Name of the style to use
            generate_description: Whether to generate AI description
            custom_ai_description: Custom AI description to use instead of generating
            temperature: Temperature for AI generation
            custom_style: Optional custom style string
            
        Returns:
            Dict[str, Any]: Dictionary containing the prompt and metadata
        """
        try:
            # Import the PromptGenerator using the correct path
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'prompt_gen'))
            from prompt_generator import PromptGenerator
            
            # Initialize the PromptGenerator with the current model
            prompt_gen = PromptGenerator(model=self.model)
            
            # Generate the complete prompt
            result = prompt_gen.generate_complete_prompt(
                character_name=character_name,
                style_name=style_name,
                generate_description=generate_description,
                custom_ai_description=custom_ai_description,
                temperature=temperature,
                custom_style=custom_style
            )
            
            logger.info(f"Generated complete prompt for '{character_name}' with style '{style_name}'")
            return result
            
        except Exception as e:
            logger.error(f"Error generating complete character prompt: {e}")
            return {
                "character_name": character_name,
                "style_name": style_name,
                "prompt": None,
                "ai_description": None,
                "success": False,
                "error": str(e)
            }