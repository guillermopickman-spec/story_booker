#!/usr/bin/env python3
"""
Example script demonstrating the use of Ollama for character description generation.
"""
import os
import sys

# Add modules to path
sys.path.insert(0, "modules")

from characters.description_gen.manager import DescriptionGenManager


def main():
    """Demonstrate description generation capabilities."""
    print("=" * 60)
    print("Ollama Character Description Generator")
    print("=" * 60)
    
    # Initialize the description manager
    manager = DescriptionGenManager()
    
    # Check if Ollama is running
    if not manager.check_ollama_connection():
        print("\n❌ Ollama is not accessible!")
        print("Please make sure Ollama is installed and running.")
        print("Download from: https://ollama.ai/")
        print("\nTo start Ollama:")
        print("  - Windows: ollama serve")
        print("  - macOS: brew services start ollama")
        print("  - Linux: systemctl start ollama")
        return
    
    print("\n✅ Ollama is accessible!")
    
    # Example 1: Basic description
    print("\n" + "-" * 40)
    print("Example 1: Basic Description")
    print("-" * 40)
    
    prompt = "Describe a mysterious ancient library filled with magical books"
    description = manager.generate_description(prompt)
    
    if description:
        print(f"\nPrompt: {prompt}")
        print(f"\nDescription:\n{description}")
    else:
        print("❌ Failed to generate description")
    
    # Example 2: Modular description
    print("\n" + "-" * 40)
    print("Example 2: Modular Character Description")
    print("-" * 40)
    
    character_name = "Zephyr Windwhisper"
    aspects = ["appearance", "personality", "background", "special abilities"]
    style = "steampunk, detailed, mechanical elements"
    
    modular_desc = manager.generate_modular_description(
        character_name=character_name,
        aspects=aspects,
        style=style
    )
    
    if modular_desc:
        print(f"\nCharacter: {character_name}")
        print(f"Style: {style}")
        print("\nModular Description:")
        print("-" * 20)
        
        for aspect, content in modular_desc.items():
            print(f"\n{aspect.upper()}:")
            print(content)
    else:
        print("❌ Failed to generate modular description")
    
    # Example 3: ComfyUI formatting
    print("\n" + "-" * 40)
    print("Example 3: ComfyUI Prompt Formatting")
    print("-" * 40)
    
    sample_description = "A young sorceress with flowing purple hair and glowing runes on her skin"
    
    formatted = manager.format_for_comfyui(
        description=sample_description,
        positive_prompt="fantasy art, digital painting",
        negative_prompt="photorealistic, realistic photo"
    )
    
    print(f"\nOriginal Description: {sample_description}")
    print(f"\nFormatted for ComfyUI:")
    print("-" * 20)
    print(f"Positive: {formatted['positive']}")
    print(f"\nNegative: {formatted['negative']}")
    
    # Example 4: Available models
    print("\n" + "-" * 40)
    print("Example 4: Available Models")
    print("-" * 40)
    
    models = manager.get_available_models()
    if models:
        print("Available Ollama models:")
        for model in models[:5]:  # Show first 5 models
            print(f"  - {model['name']}")
        if len(models) > 5:
            print(f"  ... and {len(models) - 5} more")
    else:
        print("❌ Could not retrieve models")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()