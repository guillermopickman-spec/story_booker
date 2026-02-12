#!/usr/bin/env python3
"""
Example script demonstrating the prompt generation functionality.
"""
import os
import sys

# Add modules to path
sys.path.insert(0, "modules")

from characters.description_gen.prompt_gen import PromptGenerator, PromptBuilder, DescriptionGenerator


def main():
    """Demonstrate prompt generation capabilities."""
    print("=" * 60)
    print("Character Prompt Generation Example")
    print("=" * 60)
    
    # Initialize the prompt generator
    prompt_gen = PromptGenerator()
    
    # Check if Ollama is running
    if not prompt_gen.check_connection():
        print("\n❌ Ollama is not accessible!")
        print("Please make sure Ollama is installed and running.")
        print("Download from: https://ollama.ai/")
        print("\nTo start Ollama:")
        print("  - Windows: ollama serve")
        print("  - macOS: brew services start ollama")
        print("  - Linux: systemctl start ollama")
        return
    
    print("\n✅ Ollama is accessible!")
    
    # Example 1: Generate a complete prompt
    print("\n" + "-" * 40)
    print("Example 1: Complete Prompt Generation")
    print("-" * 40)
    
    character_name = "Luna Starweaver"
    style_name = "anime"
    
    print(f"Character: {character_name}")
    print(f"Style: {style_name}")
    
    result = prompt_gen.generate_complete_prompt(
        character_name=character_name,
        style_name=style_name,
        generate_description=True,
        temperature=0.7
    )
    
    if result["success"]:
        print("\n✅ Prompt generated successfully!")
        print(f"AI Description: {result['ai_description'][:100]}...")
        print(f"\nFinal Prompt:")
        print("-" * 20)
        print(result["prompt"])
    else:
        print("❌ Failed to generate prompt")
        if "error" in result:
            print(f"Error: {result['error']}")
    
    # Example 2: Show available styles
    print("\n" + "-" * 40)
    print("Example 2: Available Styles")
    print("-" * 40)
    
    available_styles = prompt_gen.get_available_styles()
    print("Available styles:")
    for style in available_styles:
        print(f"  - {style}")
    
    # Example 3: Manual prompt building
    print("\n" + "-" * 40)
    print("Example 3: Manual Prompt Building")
    print("-" * 40)
    
    builder = PromptBuilder()
    
    # Custom description
    custom_description = "A young elven sorceress with silver hair and glowing blue eyes"
    
    # Build prompt manually
    manual_prompt = builder.build_prompt(
        character_name="Elara Moonwhisper",
        style_name="anime",
        ai_description=custom_description
    )
    
    print(f"Character: Elara Moonwhisper")
    print(f"Custom Description: {custom_description}")
    print(f"\nManually Built Prompt:")
    print("-" * 20)
    print(manual_prompt)
    
    # Example 4: Show the format we're aiming for
    print("\n" + "-" * 40)
    print("Example 4: Final Mock Prompt Format")
    print("-" * 40)
    
    # This is the format we want:
    # "(character sheet:1.3), full body, + [AI description] + , ([Style Selected] style:1.2), white background"
    
    print("\nTarget format:")
    print("(character sheet:1.3), full body, + [AI description] + , ([Style Selected] style:1.2), white background")
    
    print("\nOur current implementation achieves this format by combining:")
    print("- start.txt: '(character sheet:1.3), full body, '")
    print("- AI description: ', + [AI description] +'")
    print("- style: ', ([Style Selected] style:1.2)'")
    print("- end.txt: ', white background'")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()