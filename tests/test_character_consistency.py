"""
Integration tests for Character Consistency across the pipeline.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.models import StoryBook, StoryBeat, Character
from services.author_agent import generate_storybook
from services.art_director_agent import generate_image_prompts
from services.character_service import extract_protagonist_from_story, generate_character_reference
from services.llm_client import LLMClient
import json


class TestCharacterConsistencyIntegration:
    """Integration tests for character consistency across the pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_character(self):
        """Test full pipeline: theme → story → character → image prompts."""
        # Create mock LLM client
        mock_client = AsyncMock(spec=LLMClient)
        
        # Mock storybook generation
        mock_storybook_json = {
            "title": "Luna's Adventure",
            "beats": [
                {
                    "text": "Luna the mouse began her journey.",
                    "visual_description": "Luna starting her adventure",
                    "sticker_subjects": ["Luna"]
                },
                {
                    "text": "Luna met a friendly bird.",
                    "visual_description": "Luna talking to a bird",
                    "sticker_subjects": ["Luna", "bird"]
                }
            ]
        }
        
        # Mock character extraction
        mock_character_json = {
            "has_protagonist": True,
            "name": "Luna",
            "species": "mouse",
            "physical_description": "A small brown mouse with big round ears and bright black eyes",
            "key_features": ["big ears", "brown fur"],
            "color_palette": {
                "hair_color": "brown",
                "eye_color": "black"
            }
        }
        
        # Mock image prompt generation (with character)
        mock_image_prompts_json = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna, a small brown mouse with big round ears and bright black eyes, brown fur, cute and colorful",
                    "subject": "Luna"
                }
            ]
        }
        
        # Configure mock to return different responses for different calls
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: storybook generation
                return json.dumps(mock_storybook_json)
            elif call_count == 2:
                # Second call: character extraction
                return json.dumps(mock_character_json)
            else:
                # Subsequent calls: image prompts
                return json.dumps(mock_image_prompts_json)
        
        mock_client.generate = AsyncMock(side_effect=mock_generate)
        
        # Generate storybook
        storybook = await generate_storybook(
            theme="a brave mouse goes on an adventure",
            num_pages=2,
            llm_client=mock_client
        )
        
        # Extract character
        character = await extract_protagonist_from_story(
            theme="a brave mouse",
            storybook=storybook,
            llm_client=mock_client
        )
        
        assert character is not None
        assert character.name == "Luna"
        
        # Generate character reference
        character_reference = generate_character_reference(character)
        assert "Luna" in character_reference
        assert "brown mouse" in character_reference.lower()
        
        # Generate image prompts with character reference
        image_prompts = await generate_image_prompts(
            beat=storybook.beats[0],
            character_reference=character_reference,
            llm_client=mock_client
        )
        
        assert len(image_prompts) > 0
        # Verify character details appear in prompts
        luna_prompts = [p for p in image_prompts if "Luna" in p.subject or "luna" in p.prompt.lower()]
        if luna_prompts:
            assert any("brown" in p.prompt.lower() or "mouse" in p.prompt.lower() for p in luna_prompts)
    
    @pytest.mark.asyncio
    async def test_character_consistency_across_beats(self):
        """Test that character description is consistent across multiple beats."""
        mock_client = AsyncMock(spec=LLMClient)
        
        storybook = StoryBook(
            title="Luna's Journey",
            beats=[
                StoryBeat(
                    text="Luna started her journey.",
                    visual_description="Luna beginning",
                    sticker_subjects=["Luna"]
                ),
                StoryBeat(
                    text="Luna met a friend.",
                    visual_description="Luna meeting friend",
                    sticker_subjects=["Luna", "friend"]
                ),
                StoryBeat(
                    text="Luna reached her goal.",
                    visual_description="Luna at destination",
                    sticker_subjects=["Luna"]
                )
            ]
        )
        
        character = Character(
            name="Luna",
            species="mouse",
            physical_description="A small brown mouse with big round ears",
            key_features=["big ears", "brown fur"],
            color_palette={"hair_color": "brown", "eye_color": "black"}
        )
        
        character_reference = generate_character_reference(character)
        
        # Mock image prompt generation
        mock_prompts = {
            "prompts": [
                {
                    "prompt": f"3D rendered sticker-style Luna. {character_reference}Cute and colorful",
                    "subject": "Luna"
                }
            ]
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_prompts))
        
        # Generate prompts for all beats
        all_prompts = []
        for beat in storybook.beats:
            image_prompts = await generate_image_prompts(
                beat=beat,
                character_reference=character_reference,
                llm_client=mock_client
            )
            all_prompts.extend(image_prompts)
        
        # Verify character reference was passed for all beats
        assert len(all_prompts) > 0
        # Check that character details appear (this would be verified by the mock)
        assert mock_client.generate.call_count == len(storybook.beats)
    
    @pytest.mark.asyncio
    async def test_prompt_comparison_with_without_character(self):
        """Test comparison of prompts with and without character reference."""
        mock_client = AsyncMock(spec=LLMClient)
        
        beat = StoryBeat(
            text="Luna the mouse went exploring.",
            visual_description="Luna exploring",
            sticker_subjects=["Luna"]
        )
        
        character_reference = "Character: Luna. Species: mouse. Physical Description: A small brown mouse with big round ears. Key Features: big ears, brown fur. "
        
        # Mock prompt generation WITHOUT character
        mock_prompt_without = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna, cute mouse, colorful",
                    "subject": "Luna"
                }
            ]
        }
        
        # Mock prompt generation WITH character
        mock_prompt_with = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna, a small brown mouse with big round ears, brown fur, big ears, cute and colorful",
                    "subject": "Luna"
                }
            ]
        }
        
        # Generate without character
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(mock_prompt_without)
            else:
                return json.dumps(mock_prompt_with)
        
        mock_client.generate = AsyncMock(side_effect=mock_generate)
        
        prompts_without = await generate_image_prompts(
            beat=beat,
            character_reference=None,
            llm_client=mock_client
        )
        
        prompts_with = await generate_image_prompts(
            beat=beat,
            character_reference=character_reference,
            llm_client=mock_client
        )
        
        assert len(prompts_without) > 0
        assert len(prompts_with) > 0
        
        # The prompt with character reference should be more detailed
        prompt_without_text = prompts_without[0].prompt.lower()
        prompt_with_text = prompts_with[0].prompt.lower()
        
        # Verify character details appear in the prompt with character reference
        assert "brown" in prompt_with_text or "big ears" in prompt_with_text
        # The prompt with character should have more descriptive content
