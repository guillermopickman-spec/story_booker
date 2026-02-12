#!/usr/bin/env python3
"""
Simple test for the prompt generation functionality.
"""
import os
import sys
import unittest

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'modules'))

# Import directly from the files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'modules', 'characters', 'description_gen', 'prompt-gen'))


class TestPromptBuilder(unittest.TestCase):
    """Test cases for PromptBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid issues with module resolution
        from builder import PromptBuilder
        self.builder = PromptBuilder()
    
    def test_initialization(self):
        """Test PromptBuilder initialization."""
        self.assertIsNotNone(self.builder.start_template)
        self.assertIsNotNone(self.builder.end_template)
        self.assertIsInstance(self.builder.available_styles, dict)
    
    def test_available_styles(self):
        """Test getting available styles."""
        styles = self.builder.get_available_styles()
        self.assertIsInstance(styles, list)
        self.assertIn("anime", styles)
    
    def test_build_prompt_with_ai_description(self):
        """Test building a prompt with AI description."""
        character_name = "Test Character"
        style_name = "anime"
        ai_description = "A mysterious figure with a cloak"
        
        prompt = self.builder.build_prompt(
            character_name=character_name,
            style_name=style_name,
            ai_description=ai_description
        )
        
        self.assertNotIn(character_name, prompt)
        self.assertIn(ai_description, prompt)
        self.assertIn("storybook anime style:1.2", prompt)
    
    def test_build_prompt_without_ai_description(self):
        """Test building a prompt without AI description."""
        character_name = "Test Character"
        style_name = "anime"
        
        prompt = self.builder.build_prompt(
            character_name=character_name,
            style_name=style_name
        )
        
        self.assertNotIn(character_name, prompt)
        self.assertIn("storybook anime style:1.2", prompt)
        self.assertIn("white background", prompt)
    
    def test_validate_style(self):
        """Test style validation."""
        self.assertTrue(self.builder.validate_style("anime"))
        self.assertFalse(self.builder.validate_style("nonexistent_style"))


def test_prompt_format():
    """Test that the prompt format matches the expected format."""
    print("\n" + "=" * 60)
    print("Testing Prompt Format")
    print("=" * 60)
    
    # Import here to avoid issues with module resolution
    from builder import PromptBuilder
    
    builder = PromptBuilder()
    
    # Test the format with a custom description
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
    print("-" * 20)
    print(prompt)
    
    # Verify the format matches the expected pattern
    expected_patterns = [
        "(character sheet:1.3)",
        "full body",
        ai_description,
        "storybook anime style:1.2",
        "white background"
    ]
    
    print("\n" + "=" * 60)
    print("Format Verification")
    print("=" * 60)
    
    all_match = True
    for pattern in expected_patterns:
        if pattern in prompt:
            print(f"[FOUND] {pattern}")
        else:
            print(f"[MISSING] {pattern}")
            all_match = False
    
    if all_match:
        print("\n[SUCCESS] All expected patterns found in the prompt!")
        print("\nThis matches the requested format for image generation:")
        print("(character sheet:1.3), full body, AI_DESCRIPTION, STYLE, white background")
    else:
        print("\n[ERROR] Some expected patterns were missing.")
    
    return all_match


def main():
    """Run the tests."""
    print("=" * 60)
    print("Simple Prompt Generation Test")
    print("=" * 60)
    
    # Run unit tests
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPromptBuilder))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Test the prompt format
    format_test_passed = test_prompt_format()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Unit tests: {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    print(f"Format test: {'PASSED' if format_test_passed else 'FAILED'}")
    
    if result.wasSuccessful() and format_test_passed:
        print("\n[SUCCESS] All tests PASSED!")
        return 0
    else:
        print("\n[FAILED] Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())