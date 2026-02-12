"""
Integration tests for ComfyUI connection.
Run these tests when ComfyUI is actually running on port 8188.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from modules.characters.image_gen.client import ComfyClient


class TestComfyUIIntegration(unittest.TestCase):
    """Integration tests that require a running ComfyUI server."""
    
    def setUp(self):
        """Set up the client with default settings."""
        self.client = ComfyClient(port="8188")
    
    def test_check_connection_real(self):
        """Test actual connection to ComfyUI server."""
        self.assertTrue(self.client.check_connection(), 
                       "Could not connect to ComfyUI at http://127.0.0.1:8188")
    
    def test_queue_prompt_real(self):
        """Test sending a real workflow to ComfyUI."""
        # This is a minimal valid ComfyUI workflow
        workflow = {
            "3": {
                "inputs": {},
                "class_type": "LoadCheckpoints",
                "_meta": {
                    "title": "Load Checkpoints"
                }
            }
        }
        
        result = self.client.queue_prompt(workflow)
        
        # We expect a prompt ID to be returned
        self.assertIsNotNone(result, "Failed to queue prompt")
        self.assertIn("prompt_id", result or {}, "Response doesn't contain prompt_id")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ComfyUI Integration Tests")
    print("="*60)
    print("\nThese tests require ComfyUI to be running on port 8188")
    print("Start ComfyUI with: docker run -p 8188:8188 comfyui/comfyui")
    print("\n" + "="*60 + "\n")
    
    unittest.main(verbosity=2)