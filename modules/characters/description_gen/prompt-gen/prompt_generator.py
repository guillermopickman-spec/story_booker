#!/usr/bin/env python3
"""
Main Prompt Generator class that combines description generation and prompt building.
"""
import logging
from typing import Optional, Dict, List, Any

from .builder import PromptBuilder
from .description import DescriptionGenerator

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Main class that combines AI description generation with prompt building.
    
    This class provides a high-level interface for generating complete character prompts
    that are ready for image generation.
    """
    
    def __init__(self, model: Optional[str] = None, styles_dir: Optional[str] = None):
        """
        Initialize the PromptGenerator.
        
        Args:
            model: Model to use for AI generation. If None, uses default.
            styles_dir: Directory containing style templates. If None, uses default.
        """
        # Initialize components
        self.builder = PromptBuilder(styles_dir=styles_dir)
        self.description_generator = DescriptionGenerator(model=model)
        
        logger.info("PromptGenerator initialized")
    
    def check_connection(self) -> bool:
        """
        Check if the AI model is accessible.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.description_generator.check_connection()
    
    def get_available_styles(self) -> List[str]:
        """
        Get list of available styles.
        
        Returns:
            List[str]: List of available style names
        """
        return self.builder.get_available_styles()
    
    def get_available_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available models from Ollama.
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of model information or None if error
        """
        return self.description_generator.get_available_models()
    
    def generate_complete_prompt(self,
                               character_name: str,
                               style_name: str = "anime",
                               generate_description: bool = True,
                               custom_ai_description: Optional[str] = None,
                               generate_traits: bool = False,
                               num_traits: int = 5,
                               temperature: float = 0.7,
                               custom_style: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete character prompt.
        
        Args:
            character_name: Name of the character
            style_name: Name of the style to use
            generate_description: Whether to generate AI description
            custom_ai_description: Custom AI description to use instead of generating
            generate_traits: Whether to generate character traits
            num_traits: Number of traits to generate if generate_traits is True
            temperature: Temperature for AI generation
            custom_style: Optional custom style string
            
        Returns:
            Dict[str, Any]: Dictionary containing the prompt and metadata
        """
        result = {
            "character_name": character_name,
            "style_name": style_name,
            "prompt": None,
            "ai_description": None,
            "traits": None,
            "success": False
        }
        
        # Check connection first
        if not self.check_connection():
            logger.error("Cannot generate prompt: Ollama is not accessible")
            return result
        
        try:
            # Generate AI description if requested
            if generate_description and not custom_ai_description:
                logger.info(f"Generating AI description for '{character_name}'")
                result["ai_description"] = self.description_generator.generate_character_description(
                    character_name=character_name,
                    style=style_name,
                    temperature=temperature
                )
            elif custom_ai_description:
                result["ai_description"] = custom_ai_description
                logger.info(f"Using custom AI description for '{character_name}'")
            
            # Generate traits if requested
            if generate_traits:
                logger.info(f"Generating traits for '{character_name}'")
                result["traits"] = self.description_generator.generate_character_traits(
                    character_name=character_name,
                    style=style_name,
                    num_traits=num_traits
                )
            
            # Build the complete prompt
            logger.info(f"Building prompt for '{character_name}' with style '{style_name}'")
            result["prompt"] = self.builder.build_prompt(
                character_name=character_name,
                style_name=style_name,
                ai_description=result["ai_description"],
                custom_style=custom_style
            )
            
            result["success"] = True
            logger.info(f"Successfully generated complete prompt for '{character_name}'")
            
        except Exception as e:
            logger.error(f"Error generating complete prompt: {e}")
            result["error"] = str(e)
        
        return result
    
    def generate_character_profile_and_prompt(self,
                                            character_name: str,
                                            style_name: str = "anime",
                                            aspects: Optional[List[str]] = None,
                                            custom_style: Optional[str] = None,
                                            temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a character profile and then build a prompt from it.
        
        Args:
            character_name: Name of the character
            style_name: Name of the style to use
            aspects: List of aspects to include in the profile
            custom_style: Optional custom style string
            temperature: Temperature for AI generation
            
        Returns:
            Dict[str, Any]: Dictionary containing the profile, prompt, and metadata
        """
        result = {
            "character_name": character_name,
            "style_name": style_name,
            "profile": None,
            "prompt": None,
            "success": False
        }
        
        # Check connection first
        if not self.check_connection():
            logger.error("Cannot generate profile and prompt: Ollama is not accessible")
            return result
        
        try:
            # Generate character profile
            logger.info(f"Generating profile for '{character_name}'")
            profile = self.description_generator.generate_full_character_profile(
                character_name=character_name,
                style=style_name,
                aspects=aspects
            )
            
            if profile:
                result["profile"] = profile
                
                # Combine all aspects into a single description
                combined_description = ". ".join([f"{aspect}: {content}" for aspect, content in profile.items()])
                
                # Build the complete prompt
                logger.info(f"Building prompt from profile for '{character_name}'")
                result["prompt"] = self.builder.build_prompt(
                    character_name=character_name,
                    style_name=style_name,
                    ai_description=combined_description,
                    custom_style=custom_style
                )
                
                result["success"] = True
                logger.info(f"Successfully generated profile and prompt for '{character_name}'")
            else:
                result["error"] = "Failed to generate character profile"
                
        except Exception as e:
            logger.error(f"Error generating profile and prompt: {e}")
            result["error"] = str(e)
        
        return result
    
    def set_model(self, model: str) -> None:
        """
        Change the model used for AI generation.
        
        Args:
            model: New model name
        """
        self.description_generator.set_model(model)
        logger.info(f"Changed model to: {model}")
    
    def validate_style(self, style_name: str) -> bool:
        """
        Check if a style is available.
        
        Args:
            style_name: Name of the style to check
            
        Returns:
            bool: True if style is available, False otherwise
        """
        return self.builder.validate_style(style_name)
    
    def get_style_content(self, style_name: str) -> Optional[str]:
        """
        Get the content of a specific style.
        
        Args:
            style_name: Name of the style to get
            
        Returns:
            Optional[str]: Style content or None if not found
        """
        return self.builder.get_style_content(style_name)