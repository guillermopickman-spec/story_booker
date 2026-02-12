#!/usr/bin/env python3
"""
Prompt Builder module for generating character prompts.
"""
import os
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds character prompts by combining templates and styles."""
    
    def __init__(self, styles_dir: Optional[str] = None):
        """
        Initialize the PromptBuilder.
        
        Args:
            styles_dir: Directory containing style templates. If None, uses default.
        """
        self.styles_dir = styles_dir or os.path.join(os.path.dirname(__file__), "styles")
        self.start_template = self._load_template("start.txt")
        self.end_template = self._load_template("end.txt")
        self.available_styles = self._load_styles()
        
        logger.info(f"PromptBuilder initialized with {len(self.available_styles)} available styles")
    
    def _load_template(self, filename: str) -> str:
        """Load a template file."""
        template_path = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load template {filename}: {e}")
            return ""
    
    def _load_styles(self) -> Dict[str, str]:
        """Load all available styles from the styles directory."""
        styles = {}
        
        if not os.path.exists(self.styles_dir):
            logger.warning(f"Styles directory not found: {self.styles_dir}")
            return styles
        
        for filename in os.listdir(self.styles_dir):
            if filename.endswith('.txt'):
                style_name = filename[:-4]  # Remove .txt extension
                style_path = os.path.join(self.styles_dir, filename)
                try:
                    with open(style_path, 'r', encoding='utf-8') as f:
                        styles[style_name] = f.read().strip()
                except Exception as e:
                    logger.error(f"Failed to load style {filename}: {e}")
        
        logger.info(f"Loaded {len(styles)} styles: {list(styles.keys())}")
        return styles
    
    def get_available_styles(self) -> List[str]:
        """Get list of available style names."""
        return list(self.available_styles.keys())
    
    def build_prompt(self, 
                    character_name: str,
                    style_name: str = "anime",
                    ai_description: Optional[str] = None,
                    custom_style: Optional[str] = None) -> str:
        """
        Build a complete character prompt.
        
        Args:
            character_name: Name of the character (not included in final prompt)
            style_name: Name of the style to use (from available styles)
            ai_description: AI-generated character description
            custom_style: Optional custom style string
            
        Returns:
            str: Complete prompt formatted for image generation
        """
        # Get style information
        style_content = ""
        if custom_style:
            style_content = custom_style
        elif style_name in self.available_styles:
            style_content = self.available_styles[style_name]
        else:
            logger.warning(f"Style '{style_name}' not found, using default")
            style_content = self.available_styles.get("anime", "")
        
        # Build the prompt components
        start_part = self.start_template
        ai_part = f", {ai_description}" if ai_description else ""
        style_part = f", {style_content}" if style_content else ""
        end_part = self.end_template
        
        # Combine all parts
        full_prompt = f"{start_part}{ai_part}{style_part}{end_part}"
        
        logger.info(f"Built prompt with style '{style_name}'")
        return full_prompt
    
    def validate_style(self, style_name: str) -> bool:
        """Check if a style is available."""
        return style_name in self.available_styles
    
    def get_style_content(self, style_name: str) -> Optional[str]:
        """Get the content of a specific style."""
        return self.available_styles.get(style_name)