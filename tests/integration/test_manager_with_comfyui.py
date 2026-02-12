"""
Integration tests for ImageGenManager with real ComfyUI.
Run these tests when ComfyUI is actually running on port 8188.
"""
import sys
import os
import time
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.characters.image_gen.manager import ImageGenManager


class TestImageGenManagerWithComfyUI(unittest.TestCase):
    """Integration tests that require a running ComfyUI server."""
    
    def setUp(self):
        """Set up the manager with default settings."""
        self.manager = ImageGenManager(workflow_name="character_creator")
    
    def test_manager_connection(self):
        """Test manager can connect to ComfyUI server."""
        self.assertTrue(self.manager.check_comfyui_connection(), 
                       "Could not connect to ComfyUI server")
    
    def test_firefighter_dog_concept_art(self):
        """Test generating a firefighter dog concept art image."""
        # Firefighter dog concept art prompt
        positive_prompt = "A heroic Dalmatian firefighter dog wearing a custom fire helmet and small jacket, standing confidently in front of a fire truck, detailed fur texture, expressive eyes, cinematic lighting, digital painting style, concept art"
        negative_prompt = "low quality, blurry, distorted, extra limbs, bad anatomy, cartoon, childish, text, watermark, signature, deformed"
        
        # Test workflow generation
        workflow = self.manager.get_workflow(user_pos=positive_prompt, user_neg=negative_prompt)
        self.assertIsNotNone(workflow, "Failed to generate workflow")
        self.assertGreater(len(workflow), 0, "Workflow should have nodes")
        
        # Test image generation
        result = self.manager.generate_image(user_pos=positive_prompt, user_neg=negative_prompt)
        self.assertIsNotNone(result, "Failed to generate image")
        self.assertIsInstance(result, dict, "Response should be a dictionary")
        self.assertIn("prompt_id", result, "Response should contain prompt_id")
        
        # Store prompt ID for status check
        prompt_id = result["prompt_id"]
        
        # Check status after a short delay
        time.sleep(2)  # Wait for processing to start
        status = self.manager.get_status(prompt_id)
        self.assertIsNotNone(status, "Failed to get prompt status")
        
        # Print status information
        print(f"\nFirefighter dog concept art generation started:")
        print(f"Prompt ID: {prompt_id}")
        print(f"Status: {status}")
    
    def test_workflow_composition(self):
        """Test workflow composition with different prompts."""
        # Test with different character concepts
        test_prompts = [
            ("A brave German Shepherd police dog, wearing a police vest, ready for duty", "blurry, low quality"),
            ("A playful Golden Retriever therapy dog, gentle expression", "distorted, bad anatomy"),
            ("A strong Siberian Husky sled dog, in arctic gear", "blurry, cartoonish")
        ]
        
        for pos_prompt, neg_prompt in test_prompts:
            with self.subTest(prompt=pos_prompt):
                workflow = self.manager.get_workflow(user_pos=pos_prompt, user_neg=neg_prompt)
                self.assertIsNotNone(workflow)
                self.assertGreater(len(workflow), 0)
                
                # Verify that text nodes have been updated with prompts
                text_nodes = [node_id for node_id, node in workflow.items() 
                             if node.get("class_type") == "CLIPTextEncode"]
                self.assertGreater(len(text_nodes), 0, "Workflow should have CLIPTextEncode nodes")
                
                # Check that at least one node has our positive prompt
                prompt_found = False
                for node_id in text_nodes:
                    if "text" in workflow[node_id]["inputs"]:
                        if pos_prompt.lower() in workflow[node_id]["inputs"]["text"].lower():
                            prompt_found = True
                            break
                self.assertTrue(prompt_found, f"Positive prompt not found in workflow text nodes")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ImageGenManager ComfyUI Integration Tests")
    print("="*60)
    print("\nThese tests require ComfyUI to be running on port 8188")
    print("Start ComfyUI with: docker run -p 8188:8188 comfyui/comfyui")
    print("\nThis test will attempt to generate a firefighter dog concept art image!")
    print("\n" + "="*60 + "\n")
    
    unittest.main(verbosity=2)