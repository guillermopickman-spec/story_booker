#!/usr/bin/env python3
"""
Description Generator module for generating character descriptions using AI.
"""
import logging
from typing import Optional, Dict, List, Any

from ..client import OllamaClient

logger = logging.getLogger(__name__)


class DescriptionGenerator:
    """Generates character descriptions using AI models."""
    
    def __init__(self, model: Optional[str] = None, client: Optional[OllamaClient] = None):
        """
        Initialize the DescriptionGenerator.
        
        Args:
            model: Model to use for generation. If None, uses default.
            client: Optional OllamaClient instance. If None, creates a new one.
        """
        if client:
            self.client = client
        else:
            model_name = model or "llama3.1:8b"
            self.client = OllamaClient(model=model_name)
        
        self.model = self.client.model
        logger.info(f"DescriptionGenerator initialized with model: {self.model}")
    
    def check_connection(self) -> bool:
        """
        Check if the Ollama client is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.client.check_connection()
    
    def generate_character_description(self, 
                                     character_name: str,
                                     style: Optional[str] = None,
                                     traits: Optional[List[str]] = None,
                                     temperature: float = 0.7) -> Optional[str]:
        """
        Generate a character description using AI.
        
        Args:
            character_name: Name of the character
            style: Optional style guidance
            traits: List of character traits to include
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Optional[str]: Generated character description or None if error
        """
        if not self.check_connection():
            logger.error("Cannot generate description: Ollama is not accessible")
            return None
        
        # Build the prompt
        prompt = self._build_character_prompt(character_name, style, traits)
        
        try:
            response = self.client.generate(prompt, temperature=temperature)
            
            if response and "response" in response:
                description = response["response"].strip()
                logger.info(f"Generated description for '{character_name}' ({len(description)} chars)")
                return description
            else:
                logger.error("Invalid response from Ollama")
                return None
                
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return None
    
    def generate_character_traits(self, 
                                 character_name: str,
                                 style: Optional[str] = None,
                                 num_traits: int = 5) -> Optional[List[str]]:
        """
        Generate a list of character traits.
        
        Args:
            character_name: Name of the character
            style: Optional style guidance
            num_traits: Number of traits to generate
            
        Returns:
            Optional[List[str]]: List of character traits or None if error
        """
        if not self.check_connection():
            logger.error("Cannot generate traits: Ollama is not accessible")
            return None
        
        # Build the prompt
        prompt = f"Generate {num_traits} distinctive character traits for '{character_name}'. "
        
        if style:
            prompt += f"The style should be: {style}. "
            
        prompt += "Return only the traits, one per line, with no additional text or formatting."
        
        try:
            response = self.client.generate(prompt, temperature=0.7)
            
            if response and "response" in response:
                trait_text = response["response"].strip()
                # Split by lines and clean up each trait
                traits = [trait.strip() for trait in trait_text.split('\n') if trait.strip()]
                
                # Limit to requested number of traits
                traits = traits[:num_traits]
                
                logger.info(f"Generated {len(traits)} traits for '{character_name}'")
                return traits
            else:
                logger.error("Invalid response from Ollama")
                return None
                
        except Exception as e:
            logger.error(f"Error generating traits: {e}")
            return None
    
    def generate_full_character_profile(self,
                                      character_name: str,
                                      style: Optional[str] = None,
                                      aspects: Optional[List[str]] = None) -> Optional[Dict[str, str]]:
        """
        Generate a complete character profile with multiple aspects.
        
        Args:
            character_name: Name of the character
            style: Optional style guidance
            aspects: List of aspects to include (appearance, personality, background, etc.)
            
        Returns:
            Optional[Dict[str, str]]: Dictionary with character aspects or None if error
        """
        # Default aspects if not specified
        default_aspects = ["appearance", "personality", "background", "special abilities"]
        aspects = aspects or default_aspects
        
        if not self.check_connection():
            logger.error("Cannot generate profile: Ollama is not accessible")
            return None
        
        # Build the system prompt
        system_prompt = """You are a creative writer specializing in character descriptions.
        Generate detailed, vivid descriptions for character aspects.
        Focus on creating evocative, original content that would be useful for image generation.
        Return your response as a JSON object with keys matching the requested aspects."""
        
        # Build the main prompt
        prompt = f"Generate a detailed character profile for '{character_name}'. "
        
        if style:
            prompt += f"The style should be: {style}. "
            
        prompt += f"Please provide descriptions for the following aspects: {', '.join(aspects)}. "
        prompt += "Return your response as a JSON object with keys exactly matching the aspect names."
        
        try:
            response = self.client.generate(prompt, system=system_prompt, temperature=0.7)
            
            if response and "response" in response:
                # Parse the JSON response
                import json
                profile = json.loads(response["response"])
                
                # Ensure we have all requested aspects
                for aspect in aspects:
                    if aspect not in profile:
                        profile[aspect] = f"No {aspect} description available"
                
                logger.info(f"Generated profile for '{character_name}' with {len(profile)} aspects")
                return profile
            else:
                logger.error("Invalid response from Ollama")
                return None
                
        except Exception as e:
            logger.error(f"Error generating profile: {e}")
            return None
    
    def _build_character_prompt(self, 
                               character_name: str,
                               style: Optional[str] = None,
                               traits: Optional[List[str]] = None) -> str:
        """
        Build a prompt for character description generation.
        
        Args:
            character_name: Name of the character
            style: Optional style guidance
            traits: Optional list of character traits
            
        Returns:
            str: Complete prompt for AI generation
        """
        prompt = f"Describe the character '{character_name}' in vivid detail. "
        
        if style:
            prompt += f"The style should be: {style}. "
            
        if traits:
            prompt += f"Incorporate these traits: {', '.join(traits)}. "
            
        prompt += "Focus on visual details that would be useful for image generation. "
        prompt += "Include appearance, clothing, expression, and any distinctive features. "
        prompt += "Be creative and original."
        
        return prompt
    
    def get_available_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available models from Ollama.
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of model information or None if error
        """
        return self.client.list_models()
    
    def set_model(self, model: str) -> None:
        """
        Change the model used for generation.
        
        Args:
            model: New model name
        """
        self.client.set_model(model)
        self.model = model
        logger.info(f"Changed model to: {model}")