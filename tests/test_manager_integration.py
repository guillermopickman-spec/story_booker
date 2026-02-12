#!/usr/bin/env python3
"""
Test script to demonstrate the integration with DescriptionGenManager.
"""
import os
import sys

# Add modules to path
sys.path.insert(0, "modules")

from characters.description_gen.manager import DescriptionGenManager


def test_manager_integration():
    """Test the integration with DescriptionGenManager."""
    print("=" * 60)
    print("Testing DescriptionGenManager Integration")
    print("=" * 60)
    
    # Initialize the manager
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
    
    # Test the new method
    print("\n" + "-" * 40)
    print("Testing generate_complete_character_prompt")
    print("-" * 40)
    
    character_name = "Test Character"
    style_name = "anime"
    
    print(f"Character: {character_name}")
    print(f"Style: {style_name}")
    
    result = manager.generate_complete_character_prompt(
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
    
    # Test without AI description
    print("\n" + "-" * 40)
    print("Testing without AI description")
    print("-" * 40)
    
    result2 = manager.generate_complete_character_prompt(
        character_name=character_name,
        style_name=style_name,
        generate_description=False
    )
    
    if result2["success"]:
        print("\n✅ Prompt generated successfully!")
        print(f"\nFinal Prompt:")
        print("-" * 20)
        print(result2["prompt"])
    else:
        print("❌ Failed to generate prompt")
    
    print("\n" + "=" * 60)
    print("Integration test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_manager_integration()