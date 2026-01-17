"""
Unit tests for Character Service.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from src.models import StoryBook, StoryBeat, Character
from services.character_service import extract_protagonist_from_story, generate_character_reference
from services.llm_client import LLMClient


class TestCharacterReference:
    """Tests for character reference formatting."""
    
    def test_generate_character_reference_basic(self):
        """Test character reference formatting with basic character."""
        character = Character(
            name="Luna",
            species="mouse",
            physical_description="A small brown mouse with big round ears",
            key_features=["big ears", "brown fur"],
            color_palette={"hair_color": "brown", "eye_color": "black"}
        )
        
        reference = generate_character_reference(character)
        
        assert "Character: Luna" in reference
        assert "Species: mouse" in reference
        assert "Physical Description: A small brown mouse with big round ears" in reference
        assert "Key Features: big ears, brown fur" in reference
        assert "Colors:" in reference
        assert "brown" in reference.lower()
    
    def test_generate_character_reference_minimal(self):
        """Test character reference with minimal information."""
        character = Character(
            name="Max",
            physical_description="A brave young explorer"
        )
        
        reference = generate_character_reference(character)
        
        assert "Character: Max" in reference
        assert "Physical Description: A brave young explorer" in reference
        assert reference.endswith(". ")
    
    def test_generate_character_reference_no_colors(self):
        """Test character reference without color palette."""
        character = Character(
            name="Sam",
            species="human",
            physical_description="A tall child with short hair",
            key_features=["tall", "short hair"]
        )
        
        reference = generate_character_reference(character)
        
        assert "Character: Sam" in reference
        assert "Species: human" in reference
        assert "Key Features: tall, short hair" in reference


class TestExtractProtagonist:
    """Tests for protagonist extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_protagonist_with_mocked_client(self):
        """Test protagonist extraction with mocked LLM client."""
        mock_client = AsyncMock(spec=LLMClient)
        
        mock_character_json = {
            "has_protagonist": True,
            "name": "Luna",
            "species": "mouse",
            "physical_description": "A small brown mouse with big round ears and bright black eyes",
            "key_features": ["big ears", "brown fur", "bright eyes"],
            "color_palette": {
                "hair_color": "brown",
                "eye_color": "black",
                "skin_color": None,
                "clothing_color": "blue"
            }
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_character_json))
        
        storybook = StoryBook(
            title="Luna's Adventure",
            beats=[
                StoryBeat(
                    text="Luna the mouse went on an adventure.",
                    visual_description="Luna walking through a forest",
                    sticker_subjects=["Luna"]
                )
            ]
        )
        
        character = await extract_protagonist_from_story(
            theme="a brave mouse",
            storybook=storybook,
            llm_client=mock_client
        )
        
        assert character is not None
        assert isinstance(character, Character)
        assert character.name == "Luna"
        assert character.species == "mouse"
        assert "brown mouse" in character.physical_description.lower()
        assert "big ears" in character.key_features
        assert character.color_palette is not None
        assert character.color_palette["hair_color"] == "brown"
        
        mock_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_protagonist_no_protagonist(self):
        """Test when no clear protagonist is identified."""
        mock_client = AsyncMock(spec=LLMClient)
        
        mock_character_json = {
            "has_protagonist": False
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_character_json))
        
        storybook = StoryBook(
            title="The Forest",
            beats=[
                StoryBeat(
                    text="Many animals lived in the forest.",
                    visual_description="A forest scene",
                    sticker_subjects=["tree", "bird"]
                )
            ]
        )
        
        character = await extract_protagonist_from_story(
            theme="a forest",
            storybook=storybook,
            llm_client=mock_client
        )
        
        assert character is None
    
    @pytest.mark.asyncio
    async def test_extract_protagonist_json_parsing_error_handling(self):
        """Test error handling for malformed JSON response."""
        mock_client = AsyncMock(spec=LLMClient)
        mock_client.generate = AsyncMock(return_value="Not valid JSON")
        
        storybook = StoryBook(
            title="Test Story",
            beats=[
                StoryBeat(
                    text="Test text",
                    visual_description="Test scene",
                    sticker_subjects=["subject"]
                )
            ]
        )
        
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            await extract_protagonist_from_story(
                theme="test",
                storybook=storybook,
                llm_client=mock_client
            )
    
    @pytest.mark.asyncio
    async def test_extract_protagonist_with_wrapped_json(self):
        """Test extraction with JSON wrapped in extra text."""
        mock_client = AsyncMock(spec=LLMClient)
        
        mock_character_json = {
            "has_protagonist": True,
            "name": "Max",
            "species": "bear",
            "physical_description": "A friendly brown bear",
            "key_features": ["friendly"],
            "color_palette": None
        }
        
        wrapped_response = f"Some text {json.dumps(mock_character_json)} more text"
        mock_client.generate = AsyncMock(return_value=wrapped_response)
        
        storybook = StoryBook(
            title="Max's Story",
            beats=[
                StoryBeat(
                    text="Max was a bear.",
                    visual_description="Max in the forest",
                    sticker_subjects=["Max"]
                )
            ]
        )
        
        character = await extract_protagonist_from_story(
            theme="a bear",
            storybook=storybook,
            llm_client=mock_client
        )
        
        assert character is not None
        assert character.name == "Max"
        assert character.species == "bear"
