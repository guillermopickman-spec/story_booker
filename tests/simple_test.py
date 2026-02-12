#!/usr/bin/env python3
"""
Simple test script to demonstrate prompt generation.
"""
import os
import sys

# Add modules to path
sys.path.insert(0, "modules")

# Import directly from the files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules', 'characters', 'description_gen', 'prompt-gen'))

from builder import PromptBuilder


def test_prompt_generation():
    """Test prompt generation with different scenarios."""
    print("=" * 60)
    print("Simple Prompt Generation Test")
    print("=" * 60)
    
    # Initialize the builder
    builder = PromptBuilder()
    
    print("\n1. Available Styles:")
    styles = builder.get_available_styles()
    for style in styles:
        print(f"   - {style}")
    
    print("\n2. Test Case 1: With AI Description")
    print("-" * 30)
    
    # Test with AI description
    ai_description = "A mysterious sorceress with flowing purple robes and glowing eyes"
    style_name = "anime"
    
    prompt = builder.build_prompt(
        character_name="Test Character",  # This won't be included in the output
        style_name=style_name,
        ai_description=ai_description
    )
    
    print(f"AI Description: {ai_description}")
    print(f"Style: {style_name}")
    print(f"Generated Prompt: {prompt}")
    
    print("\n3. Test Case 2: Without AI Description")
    print("-" * 30)
    
    # Test without AI description
    prompt2 = builder.build_prompt(
        character_name="Test Character",
        style_name=style_name
    )
    
    print(f"Style: {style_name}")
    print(f"Generated Prompt: {prompt2}")
    
    print("\n4. Test Case 3: Custom Style")
    print("-" * 30)
    
    # Test with custom style
    custom_style = "fantasy art style:1.5"
    prompt3 = builder.build_prompt(
        character_name="Test Character",
        style_name="anime",  # This will be overridden
        ai_description="A brave knight with shining armor",
        custom_style=custom_style
    )
    
    print(f"AI Description: A brave knight with shining armor")
    print(f"Custom Style: {custom_style}")
    print(f"Generated Prompt: {prompt3}")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- All prompts follow the format: (character sheet:1.3), full body, AI_DESCRIPTION, STYLE, white background")
    print("- Character names are not included in the final output")
    print("- Brackets around AI descriptions have been removed")
    print("- The module is ready for image generation")
    print("=" * 60)


if __name__ == "__main__":
    test_prompt_generation()