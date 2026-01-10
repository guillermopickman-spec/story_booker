"""
Tests for Author Agent and Art Director Agent.
Includes both mocked unit tests and integration tests (when API keys are available).
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from src.models import StoryBook, StoryBeat, ImagePrompt
from services.author_agent import generate_storybook
from services.art_director_agent import generate_image_prompts
from services.llm_client import LLMClient
import os


class TestAuthorAgent:
    """Tests for Author Agent with mocking."""
    
    @pytest.mark.asyncio
    async def test_author_agent_with_mocked_client(self):
        """Test Author Agent with mocked LLM client."""
        # Create mock LLM client
        mock_client = AsyncMock(spec=LLMClient)
        
        # Mock response with valid storybook JSON
        mock_storybook_json = {
            "title": "Test Story",
            "beats": [
                {
                    "text": "Paragraph 1.\n\nParagraph 2.",
                    "visual_description": "Test scene",
                    "sticker_subjects": ["subject1"]
                }
            ] * 5  # Exactly 5 beats
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_storybook_json))
        
        # Test generation
        storybook = await generate_storybook(
            theme="test theme",
            llm_client=mock_client
        )
        
        assert isinstance(storybook, StoryBook)
        assert storybook.title == "Test Story"
        assert len(storybook.beats) == 5
        assert all(isinstance(beat, StoryBeat) for beat in storybook.beats)
        
        # Verify LLM was called correctly
        mock_client.generate.assert_called_once()
        call_args = mock_client.generate.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "test theme" in messages[1]["content"]
        assert call_args.kwargs["response_format"]["type"] == "json_object"
    
    @pytest.mark.asyncio
    async def test_author_agent_invalid_json(self):
        """Test Author Agent handles invalid JSON response."""
        mock_client = AsyncMock(spec=LLMClient)
        mock_client.generate = AsyncMock(return_value="Invalid JSON response")
        
        with pytest.raises(ValueError, match="Failed to parse"):
            await generate_storybook(
                theme="test",
                llm_client=mock_client
            )
    
    @pytest.mark.asyncio
    async def test_author_agent_wrong_beat_count(self):
        """Test Author Agent validates beat count."""
        mock_client = AsyncMock(spec=LLMClient)
        mock_storybook_json = {
            "title": "Test Story",
            "beats": [{"text": "Test", "visual_description": "Test", "sticker_subjects": ["subj"]}] * 3  # Only 3 beats
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_storybook_json))
        
        with pytest.raises(RuntimeError, match="Expected exactly 5 story beats"):
            await generate_storybook(
                theme="test",
                llm_client=mock_client
            )
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")),
        reason="No API key available - skipping integration test"
    )
    async def test_author_agent_integration(self):
        """Integration test with real LLM (requires API key)."""
        theme = "a brave little mouse"
        
        storybook = await generate_storybook(theme)
        
        assert isinstance(storybook, StoryBook)
        assert storybook.title
        assert len(storybook.title) > 0
        assert len(storybook.beats) == 5
        
        for beat in storybook.beats:
            assert isinstance(beat, StoryBeat)
            assert beat.text
            assert beat.visual_description
            assert beat.sticker_subjects
            assert len(beat.sticker_subjects) >= 1
            assert len(beat.sticker_subjects) <= 3


class TestArtDirectorAgent:
    """Tests for Art Director Agent with mocking."""
    
    @pytest.mark.asyncio
    async def test_art_director_agent_with_mocked_client(self):
        """Test Art Director Agent with mocked LLM client."""
        beat = StoryBeat(
            text="The brave mouse explored the garden.",
            visual_description="Mouse in garden",
            sticker_subjects=["mouse", "flower"]
        )
        
        mock_client = AsyncMock(spec=LLMClient)
        mock_response = {
            "prompts": [
                {"prompt": "3D rendered mouse sticker", "subject": "mouse"},
                {"prompt": "3D rendered flower sticker", "subject": "flower"}
            ]
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_response))
        
        image_prompts = await generate_image_prompts(
            beat=beat,
            llm_client=mock_client
        )
        
        assert len(image_prompts) >= len(beat.sticker_subjects)
        assert all(isinstance(p, ImagePrompt) for p in image_prompts)
        assert all(p.prompt and p.subject for p in image_prompts)
        
        # Verify LLM was called
        mock_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_art_director_agent_fallback_prompts(self):
        """Test Art Director Agent creates fallback prompts if LLM doesn't generate enough."""
        beat = StoryBeat(
            text="Test story",
            visual_description="Test scene",
            sticker_subjects=["mouse", "tree", "flower"]
        )
        
        mock_client = AsyncMock(spec=LLMClient)
        # LLM only generates 1 prompt instead of 3
        mock_response = {
            "prompts": [
                {"prompt": "3D rendered mouse sticker", "subject": "mouse"}
            ]
        }
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_response))
        
        image_prompts = await generate_image_prompts(
            beat=beat,
            llm_client=mock_client
        )
        
        # Should have 3 prompts (fallback created for missing subjects)
        assert len(image_prompts) >= len(beat.sticker_subjects)
        subjects = [p.subject for p in image_prompts]
        assert "mouse" in subjects
        # Fallback should create prompts for missing subjects
        assert len(image_prompts) == len(beat.sticker_subjects)
    
    @pytest.mark.asyncio
    async def test_art_director_agent_invalid_json(self):
        """Test Art Director Agent handles invalid JSON."""
        beat = StoryBeat(
            text="Test",
            visual_description="Test",
            sticker_subjects=["mouse"]
        )
        
        mock_client = AsyncMock(spec=LLMClient)
        mock_client.generate = AsyncMock(return_value="Invalid JSON")
        
        with pytest.raises(ValueError, match="Failed to parse"):
            await generate_image_prompts(
                beat=beat,
                llm_client=mock_client
            )
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")),
        reason="No API key available - skipping integration test"
    )
    async def test_art_director_agent_integration(self):
        """Integration test with real LLM (requires API key)."""
        beat = StoryBeat(
            text="The brave mouse explored the garden and found a shiny acorn.",
            visual_description="A small mouse standing in a colorful garden with flowers and an acorn",
            sticker_subjects=["mouse", "acorn"]
        )
        
        image_prompts = await generate_image_prompts(beat)
        
        assert len(image_prompts) >= len(beat.sticker_subjects)
        
        for prompt in image_prompts:
            assert isinstance(prompt, ImagePrompt)
            assert prompt.prompt
            assert prompt.subject
            assert len(prompt.prompt) > 0
            assert len(prompt.subject) > 0


class TestEndToEnd:
    """End-to-end tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")),
        reason="No API key available - skipping integration test"
    )
    async def test_full_storybook_generation_flow(self):
        """Test complete flow: Author Agent -> Art Director Agent."""
        theme = "a magical forest adventure"
        
        # Generate storybook
        storybook = await generate_storybook(theme)
        
        # Generate image prompts for first beat
        first_beat = storybook.beats[0]
        image_prompts = await generate_image_prompts(first_beat)
        
        # Verify results
        assert len(image_prompts) >= len(first_beat.sticker_subjects)
        # All subjects should have prompts (checking len is sufficient since fallback creates prompts)
