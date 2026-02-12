#!/usr/bin/env python3
"""
Test for the prompt generation functionality.
"""
import os
import sys
import unittest

# Add modules to path
sys.path.insert(0, "modules")

# Import the classes we want to test
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import using relative paths
from modules.characters.description_gen.prompt_gen.builder import PromptBuilder
from modules.characters.description_gen.prompt_gen.description import DescriptionGenerator
from modules.characters.description_gen.prompt_gen.prompt_generator import PromptGenerator


class TestPromptBuilder(unittest.TestCase):
    """Test cases for PromptBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
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
        
        self.assertIn(character_name, prompt)
        self.assertIn(ai_description, prompt)
        self.assertIn("(storybook anime style:1.2)", prompt)
    
    def test_build_prompt_without_ai_description(self):
        """Test building a prompt without AI description."""
        character_name = "Test Character"
        style_name = "anime"
        
        prompt = self.builder.build_prompt(
            character_name=character_name,
            style_name=style_name
        )
        
        self.assertIn(character_name, prompt)
        self.assertIn("(storybook anime style:1.2)", prompt)
        self.assertIn("white background", prompt)
    
    def test_validate_style(self):
        """Test style validation."""
        self.assertTrue(self.builder.validate_style("anime"))
        self.assertFalse(self.builder.validate_style("nonexistent_style"))


class TestDescriptionGenerator(unittest.TestCase):
    """Test cases for DescriptionGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = DescriptionGenerator()
    
    def test_initialization(self):
        """Test DescriptionGenerator initialization."""
        self.assertIsNotNone(self.generator.client)
        self.assertIsNotNone(self.generator.model)
    
    def test_check_connection(self):
        """Test connection check."""
        # This will return False if Ollama is not running
        # We're just testing the method exists and returns a boolean
        result = self.generator.check_connection()
        self.assertIsInstance(result, bool)
    
    def test_generate_character_description_no_connection(self):
        """Test description generation when Ollama is not connected."""
        # This test will pass even if Ollama is not running
        # because we expect it to return None
        result = self.generator.generate_character_description(
            character_name="Test Character"
        )
        # If Ollama is not running, result should be None
        # If Ollama is running, result should be a string
        self.assertTrue(result is None or isinstance(result, str))
    
    def test_generate_character_traits_no_connection(self):
        """Test trait generation when Ollama is not connected."""
        # This test will pass even if Ollama is not running
        # because we expect it to return None
        result = self.generator.generate_character_traits(
            character_name="Test Character"
        )
        # If Ollama is not running, result should be None
        # If Ollama is running, result should be a list
        self.assertTrue(result is None or isinstance(result, list))


class TestPromptGenerator(unittest.TestCase):
    """Test cases for PromptGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.prompt_gen = PromptGenerator()
    
    def test_initialization(self):
        """Test PromptGenerator initialization."""
        self.assertIsInstance(self.prompt_gen.builder, PromptBuilder)
        self.assertIsInstance(self.prompt_gen.description_generator, DescriptionGenerator)
    
    def test_check_connection(self):
        """Test connection check."""
        # This will return False if Ollama is not running
        # We're just testing the method exists and returns a boolean
        result = self.prompt_gen.check_connection()
        self.assertIsInstance(result, bool)
    
    def test_get_available_styles(self):
        """Test getting available styles."""
        styles = self.prompt_gen.get_available_styles()
        self.assertIsInstance(styles, list)
        self.assertIn("anime", styles)
    
    def test_generate_complete_prompt_no_connection(self):
        """Test complete prompt generation when Ollama is not connected."""
        # This test will pass even if Ollama is not running
        result = self.prompt_gen.generate_complete_prompt(
            character_name="Test Character"
        )
        
        # Should return a dict with success=False if no connection
        if result["success"] is False:
            self.assertEqual(result["character_name"], "Test Character")
            self.assertIn("success", result)
        else:
            # If Ollama is running, we expect success=True and a prompt
            self.assertTrue(result["success"])
            self.assertIsNotNone(result["prompt"])
            self.assertIsInstance(result["prompt"], str)
    
    def test_validate_style(self):
        """Test style validation."""
        self.assertTrue(self.prompt_gen.validate_style("anime"))
        self.assertFalse(self.prompt_gen.validate_style("nonexistent_style"))


class TestIntegration(unittest.TestCase):
    """Integration tests combining all components."""
    
    def test_complete_workflow_without_ollama(self):
        """Test the complete workflow without Ollama running."""
        prompt_gen = PromptGenerator()
        
        # Step 1: Get available styles
        styles = prompt_gen.get_available_styles()
        self.assertIn("anime", styles)
        
        # Step 2: Build a prompt with custom description
        builder = prompt_gen.builder
        custom_description = "A brave knight with shining armor"
        
        prompt = builder.build_prompt(
            character_name="Sir Galahad",
            style_name="anime",
            ai_description=custom_description
        )
        
        # Verify the prompt format
        self.assertIn("Sir Galahad", prompt)
        self.assertIn(custom_description, prompt)
        self.assertIn("(storybook anime style:1.2)", prompt)
        self.assertIn("white background", prompt)
        
        # Step 3: Try to generate with AI (should fail gracefully)
        result = prompt_gen.generate_complete_prompt(
            character_name="Sir Galahad",
            style_name="anime",
            generate_description=True
        )
        
        # Should handle failure gracefully
        self.assertIn("success", result)
        self.assertIn("character_name", result)
        self.assertIn("style_name", result)


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Prompt Generation Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestPromptBuilder))
    suite.addTest(unittest.makeSuite(TestDescriptionGenerator))
    suite.addTest(unittest.makeSuite(TestPromptGenerator))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests PASSED!")
        return 0
    else:
        print("\n❌ Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())