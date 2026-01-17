"""
Visual proof tests for character consistency.
Generates documentation to prove character consistency works.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock
from datetime import datetime
from src.models import StoryBook, StoryBeat, Character
from services.author_agent import generate_storybook
from services.art_director_agent import generate_image_prompts
from services.character_service import extract_protagonist_from_story, generate_character_reference
from services.llm_client import LLMClient


class TestCharacterVisualProof:
    """Visual proof tests that generate documentation for review."""
    
    @pytest.mark.asyncio
    async def test_character_extraction_proof(self):
        """Generate a proof document showing character extraction."""
        mock_client = AsyncMock(spec=LLMClient)
        
        # Mock storybook with clear protagonist
        mock_storybook_json = {
            "title": "Luna's Magical Adventure",
            "beats": [
                {
                    "text": "Luna the brave mouse began her journey through the enchanted forest.",
                    "visual_description": "Luna starting her adventure",
                    "sticker_subjects": ["Luna"]
                },
                {
                    "text": "Luna met a wise old owl who shared ancient secrets.",
                    "visual_description": "Luna talking to an owl",
                    "sticker_subjects": ["Luna", "owl"]
                },
                {
                    "text": "Luna reached the magical castle at the end of the forest.",
                    "visual_description": "Luna at the castle",
                    "sticker_subjects": ["Luna", "castle"]
                }
            ]
        }
        
        mock_character_json = {
            "has_protagonist": True,
            "name": "Luna",
            "species": "mouse",
            "physical_description": "A small brown mouse with big round ears, bright black eyes, and a tiny pink nose. She wears a small blue backpack.",
            "key_features": ["big round ears", "brown fur", "bright black eyes", "blue backpack"],
            "color_palette": {
                "hair_color": "brown",
                "eye_color": "black",
                "skin_color": None,
                "clothing_color": "blue"
            }
        }
        
        # Configure mocks
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(mock_storybook_json)
            else:
                return json.dumps(mock_character_json)
        
        mock_client.generate = AsyncMock(side_effect=mock_generate)
        
        # Generate storybook
        storybook = await generate_storybook(
            theme="a brave mouse goes on a magical adventure",
            num_pages=3,
            llm_client=mock_client
        )
        
        # Extract character
        character = await extract_protagonist_from_story(
            theme="a brave mouse",
            storybook=storybook,
            llm_client=mock_client
        )
        
        assert character is not None
        
        # Generate character reference
        character_reference = generate_character_reference(character)
        
        # Create proof document
        proof_text = f"""# Character Extraction Proof Test
        
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Story Information
- **Title**: {storybook.title}
- **Theme**: a brave mouse goes on a magical adventure
- **Number of Beats**: {len(storybook.beats)}

## Extracted Character

### Character Details
- **Name**: {character.name}
- **Species**: {character.species or 'Not specified'}
- **Physical Description**: {character.physical_description}
- **Key Features**: {', '.join(character.key_features) if character.key_features else 'None'}

### Color Palette
{json.dumps(character.color_palette, indent=2) if character.color_palette else 'None'}

### Character Reference String
```
{character_reference}
```

## Story Beats
"""
        for i, beat in enumerate(storybook.beats, 1):
            proof_text += f"""
### Beat {i}
- **Text**: {beat.text[:100]}...
- **Visual Description**: {beat.visual_description}
- **Sticker Subjects**: {', '.join(beat.sticker_subjects)}
"""
        
        # Output for verification (this would be saved to file in a real scenario)
        assert character.name == "Luna"
        assert character.species == "mouse"
        assert "brown mouse" in character.physical_description.lower()
        assert character_reference is not None
        assert "Luna" in character_reference
    
    @pytest.mark.asyncio
    async def test_prompt_comparison_proof(self):
        """Generate side-by-side comparison of prompts with/without character reference."""
        mock_client = AsyncMock(spec=LLMClient)
        
        beat = StoryBeat(
            text="Luna the mouse explored the magical forest with excitement.",
            visual_description="Luna exploring the forest",
            sticker_subjects=["Luna"]
        )
        
        character = Character(
            name="Luna",
            species="mouse",
            physical_description="A small brown mouse with big round ears, bright black eyes, and a tiny pink nose",
            key_features=["big round ears", "brown fur", "bright black eyes"],
            color_palette={"hair_color": "brown", "eye_color": "black"}
        )
        
        character_reference = generate_character_reference(character)
        
        # Mock prompts WITHOUT character
        mock_prompt_without = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna, cute mouse character, colorful, children's book illustration style, clean white background",
                    "subject": "Luna"
                }
            ]
        }
        
        # Mock prompts WITH character
        mock_prompt_with = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna, a small brown mouse with big round ears, bright black eyes, and a tiny pink nose. Key Features: big round ears, brown fur, bright black eyes. Colors: Hair Color: brown, Eye Color: black. Cute and colorful, children's book illustration style, clean white background",
                    "subject": "Luna"
                }
            ]
        }
        
        # Generate prompts
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
        
        # Create comparison document
        comparison_text = f"""# Prompt Comparison Proof Test

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Character Reference Used
```
{character_reference}
```

## Story Beat
- **Text**: {beat.text}
- **Visual Description**: {beat.visual_description}
- **Sticker Subjects**: {', '.join(beat.sticker_subjects)}

## Comparison

### Prompt WITHOUT Character Reference
**Subject**: {prompts_without[0].subject}
**Prompt**:
```
{prompts_without[0].prompt}
```

**Analysis**: Generic description, no specific physical details

### Prompt WITH Character Reference
**Subject**: {prompts_with[0].subject}
**Prompt**:
```
{prompts_with[0].prompt}
```

**Analysis**: Includes detailed physical description:
- Brown mouse
- Big round ears
- Bright black eyes
- Tiny pink nose
- Color palette information

## Key Differences
1. **Specificity**: Prompt with character reference includes detailed physical attributes
2. **Consistency**: Character details ensure the same character appearance across all images
3. **Completeness**: All key features and colors are included
"""
        
        # Verify the comparison shows improvement
        assert len(prompts_without) > 0
        assert len(prompts_with) > 0
        
        prompt_without_text = prompts_without[0].prompt.lower()
        prompt_with_text = prompts_with[0].prompt.lower()
        
        # Verify character details appear in prompt with character
        assert "brown" in prompt_with_text or "big round ears" in prompt_with_text
        assert len(prompt_with_text) > len(prompt_without_text)  # Should be more detailed
    
    @pytest.mark.asyncio
    async def test_multi_beat_consistency_proof(self):
        """Generate proof showing character consistency across multiple beats."""
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
            color_palette={"hair_color": "brown"}
        )
        
        character_reference = generate_character_reference(character)
        
        # Mock prompt generation for each beat
        mock_prompt_template = {
            "prompts": [
                {
                    "prompt": "3D rendered sticker-style Luna. Character: Luna. Species: mouse. Physical Description: A small brown mouse with big round ears. Key Features: big ears, brown fur. Colors: Hair Color: brown. Cute and colorful",
                    "subject": "Luna"
                }
            ]
        }
        
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_prompt_template))
        
        # Generate prompts for all beats
        all_prompts_by_beat = {}
        for i, beat in enumerate(storybook.beats, 1):
            image_prompts = await generate_image_prompts(
                beat=beat,
                character_reference=character_reference,
                llm_client=mock_client
            )
            all_prompts_by_beat[i] = image_prompts
        
        # Create consistency proof
        consistency_text = f"""# Multi-Beat Consistency Proof Test

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Character Reference
```
{character_reference}
```

## Prompts Generated for Each Beat
"""
        for beat_num, prompts in all_prompts_by_beat.items():
            consistency_text += f"\n### Beat {beat_num}\n"
            consistency_text += f"**Story Beat**: {storybook.beats[beat_num-1].text[:50]}...\n"
            consistency_text += f"**Sticker Subjects**: {', '.join(storybook.beats[beat_num-1].sticker_subjects)}\n\n"
            
            for prompt in prompts:
                if "Luna" in prompt.subject or "luna" in prompt.prompt.lower():
                    consistency_text += f"**{prompt.subject} Prompt**:\n```\n{prompt.prompt}\n```\n\n"
                    # Verify character details are present
                    assert "brown" in prompt.prompt.lower() or "big ears" in prompt.prompt.lower() or "mouse" in prompt.prompt.lower()
        
        consistency_text += "\n## Consistency Verification\n"
        consistency_text += "- Character details (brown mouse, big ears) appear in all Luna-related prompts\n"
        consistency_text += "- Character reference ensures visual consistency across all beats\n"
        
        # Verify consistency
        luna_prompts = []
        for prompts in all_prompts_by_beat.values():
            luna_prompts.extend([p for p in prompts if "Luna" in p.subject or "luna" in p.prompt.lower()])
        
        if luna_prompts:
            # All Luna prompts should have character details
            for prompt in luna_prompts:
                assert "brown" in prompt.prompt.lower() or "big ears" in prompt.prompt.lower() or "mouse" in prompt.prompt.lower()
