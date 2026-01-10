"""
Author Agent: Generates story beats from a theme using LLM.
"""

import json
from typing import Optional
from services.llm_client import get_llm_client, LLMClient
from src.models import StoryBook


async def generate_storybook(
    theme: str, 
    num_pages: int = 5,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    llm_client: Optional[LLMClient] = None
) -> StoryBook:
    """
    Generate a storybook with specified number of story beats from a given theme.
    
    Args:
        theme: The theme/topic for the storybook
        num_pages: Number of story beats/pages to generate (default: 5)
        provider: LLM provider to use (groq, openai, gpt4all). Defaults to groq.
        model: Model name to use (provider-specific)
        llm_client: Optional pre-configured LLM client
        
    Returns:
        StoryBook object with title and specified number of StoryBeat objects
    """
    if llm_client is None:
        llm_client = get_llm_client(provider=provider, model=model)
    system_prompt = f"""You are an expert children's book author. Your task is to create a short, 
engaging storybook suitable for ages 4-8. 

Create exactly {num_pages} story beats. Each beat should:
- Have 2 paragraphs of engaging story text (age-appropriate)
- Include a visual_description that describes what should be shown visually
- List 1-3 sticker_subjects (specific objects/characters that will appear as stickers)

The story should be cohesive, with a clear beginning, middle, and end. Make it imaginative and fun!

You MUST return valid JSON matching this exact structure:
{{
    "title": "Story Title",
    "beats": [
        {{
            "text": "Paragraph 1...\\n\\nParagraph 2...",
            "visual_description": "Description of the visual scene",
            "sticker_subjects": ["subject1", "subject2"]
        }},
        ... (exactly {num_pages} beats total)
    ]
}}"""

    user_prompt = f"Create a children's storybook with the theme: {theme or 'adventure'}\n\nGenerate exactly {num_pages} story beats.\n\nReturn only valid JSON, no additional text."

    try:
        content = await llm_client.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        
        content = content.strip()
        if content.endswith('</s>'):
            content = content[:-4].strip()
        
        try:
            story_data = json.loads(content)
        except json.JSONDecodeError:
            start_idx = content.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > start_idx:
                    json_content = content[start_idx:end_idx]
                    story_data = json.loads(json_content)
                else:
                    raise
            else:
                raise
        
        storybook = StoryBook(**story_data)
        
        if len(storybook.beats) != num_pages:
            raise ValueError(f"Expected exactly {num_pages} story beats, got {len(storybook.beats)}")
        
        return storybook
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating storybook: {e}")
