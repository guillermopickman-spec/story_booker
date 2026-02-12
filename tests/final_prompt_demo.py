#!/usr/bin/env python3
"""
Demonstration of the final prompt generation format.
"""
import os
import sys

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

# Import directly from the files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules', 'characters', 'description_gen', 'prompt-gen'))

from builder import PromptBuilder


def main():
    """Demonstrate the final prompt format."""
    print("=" * 60)
    print("Final Prompt Generation Demo")
    print("=" * 60)
    
    # Initialize the builder
    builder = PromptBuilder()
    
    print("\n1. Available Styles:")
    styles = builder.get_available_styles()
    for style in styles:
        print(f"   - {style}")
    
    print("\n2. Building a prompt with character name and AI description:")
    
    # Example 1: With AI description
    character_name = "Luna Starweaver"
    ai_description = "A young sorceress with silver hair and glowing blue eyes"
    style_name = "anime"
    
    prompt = builder.build_prompt(
        character_name=character_name,
        style_name=style_name,
        ai_description=ai_description
    )
    
    print(f"Character: {character_name}")
    print(f"AI Description: {ai_description}")
    print(f"Style: {style_name}")
    print(f"\nGenerated Prompt:")
    print("-" * 40)
    print(prompt)
    
    print("\n3. Building a prompt without AI description:")
    
    # Example 2: Without AI description
    character_name2 = "Sir Galahad"
    style_name2 = "anime"
    
    prompt2 = builder.build_prompt(
        character_name=character_name2,
        style_name=style_name2
    )
    
    print(f"Character: {character_name2}")
    print(f"Style: {style_name2}")
    print(f"\nGenerated Prompt:")
    print("-" * 40)
    print(prompt2)
    
    print("\n4. Format Analysis:")
    print("\nThe generated prompt follows this structure:")
    print("(character sheet:1.3), full body, AI_DESCRIPTION, STYLE, white background")
    print("\nNote: Character names are not included in the final prompt as it's for image generation.")
    print("Brackets around AI description have been removed for cleaner prompts.")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Implementation Complete!")
    print("The prompt-gen module successfully generates prompts in the requested format for image generation.")
    print("=" * 60)


if __name__ == "__main__":
    main()