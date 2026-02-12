import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add the modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'modules'))

from modules.characters.image_gen.workflow_composer import WorkflowComposer


class TestWorkflowComposer(unittest.TestCase):
    """Test the WorkflowComposer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables
        if "POSITIVE_PROMPT" in os.environ:
            del os.environ["POSITIVE_PROMPT"]
        if "NEGATIVE_PROMPT" in os.environ:
            del os.environ["NEGATIVE_PROMPT"]

    def tearDown(self):
        """Clean up after tests."""
        # Clear environment variables
        if "POSITIVE_PROMPT" in os.environ:
            del os.environ["POSITIVE_PROMPT"]
        if "NEGATIVE_PROMPT" in os.environ:
            del os.environ["NEGATIVE_PROMPT"]

    def test_init_with_custom_template(self):
        """Test initialization with custom template path."""
        composer = WorkflowComposer(template_path="./workflow_template.json")
        self.assertEqual(composer.template_path, "./workflow_template.json")

    def test_init_with_custom_workflow_dir(self):
        """Test initialization with custom workflow directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            composer = WorkflowComposer(workflow_dir=temp_dir)
            self.assertEqual(composer.workflow_dir, temp_dir)

    def test_init_defaults(self):
        """Test initialization uses defaults when not specified."""
        composer = WorkflowComposer()
        self.assertIsNotNone(composer.workflow_dir)
        self.assertIsNone(composer.template_path)

    def test_compose_with_env_vars(self):
        """Test composition with environment variables."""
        os.environ["POSITIVE_PROMPT"] = "high quality, masterpiece"
        os.environ["NEGATIVE_PROMPT"] = "low quality, blurry"

        composer = WorkflowComposer()
        workflow = composer.compose(
            user_pos="a beautiful sunset",
            user_neg="dark"
        )

        self.assertIsNotNone(workflow)
        # Check that positive prompt was merged
        text_nodes = [id for id, n in workflow.items() if n.get("class_type") == "CLIPTextEncode"]
        self.assertIn("a beautiful sunset", workflow["6"]["inputs"]["text"])
        self.assertIn("high quality, masterpiece", workflow["6"]["inputs"]["text"])
        # Check that negative prompt was merged
        self.assertIn("dark", workflow["7"]["inputs"]["text"])

    def test_compose_without_env_vars(self):
        """Test composition without environment variables."""
        composer = WorkflowComposer()
        workflow = composer.compose(
            user_pos="a beautiful landscape",
            user_neg="low quality"
        )

        self.assertIsNotNone(workflow)

    def test_compose_without_negative_prompt(self):
        """Test composition without negative prompt."""
        os.environ["NEGATIVE_PROMPT"] = "default negative"

        composer = WorkflowComposer()
        workflow = composer.compose(
            user_pos="test prompt",
            user_neg=None
        )

        self.assertIsNotNone(workflow)
        text_nodes = [id for id, n in workflow.items() if n.get("class_type") == "CLIPTextEncode"]
        # Should use the default from environment
        self.assertIn("default negative", workflow["7"]["inputs"]["text"])

    def test_template_caching(self):
        """Test that template is cached after first load."""
        composer = WorkflowComposer()

        # First compose should load template
        workflow1 = composer.compose(user_pos="test1")
        self.assertIsNotNone(workflow1)

        # Second compose should use cache
        workflow2 = composer.compose(user_pos="test2")
        self.assertIsNotNone(workflow2)

    def test_fallback_to_default_workflow(self):
        """Test fallback to programmatic default workflow when no file found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory but no workflow files
            composer = WorkflowComposer(workflow_dir=temp_dir)
            workflow = composer.compose(user_pos="test prompt")

            self.assertIsNotNone(workflow)
            self.assertGreater(len(workflow), 0)

    def test_find_workflow_files(self):
        """Test workflow file discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a workflow file
            workflow_file = os.path.join(temp_dir, "workflow_template.json")
            with open(workflow_file, 'w') as f:
                import json
                json.dump({"1": {"class_type": "KSampler"}}, f)

            composer = WorkflowComposer(workflow_dir=temp_dir)
            files = composer._find_workflow_files()

            self.assertEqual(len(files), 1)
            self.assertEqual(files[0], workflow_file)

    def test_preferred_workflow_names(self):
        """Test that preferred workflow names are checked first."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create workflow files with different names
            workflow_file = os.path.join(temp_dir, "default_workflow.json")
            with open(workflow_file, 'w') as f:
                import json
                json.dump({"1": {"class_type": "KSampler"}}, f)

            composer = WorkflowComposer(workflow_dir=temp_dir)
            # Should prefer default_workflow.json over other files
            self.assertEqual(composer.template_path, workflow_file)


if __name__ == '__main__':
    unittest.main()