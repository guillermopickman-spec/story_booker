"""
Author Agent: Generates story beats from a theme using LLM.
"""

import json
import logging
from typing import Optional, List
from services.llm_client import get_llm_client, LLMClient
from src.models import StoryBook, Character

logger = logging.getLogger(__name__)


async def generate_storybook(
    theme: str, 
    num_pages: int = 5,
    language: str = "en",
    characters: Optional[List[Character]] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    llm_client: Optional[LLMClient] = None
) -> StoryBook:
    """
    Generate a storybook with specified number of story beats from a given theme.
    
    Args:
        theme: The theme/topic for the storybook
        num_pages: Number of story beats/pages to generate (default: 5)
        language: Language for story generation ("en" for English, "es" for Spanish, default: "en")
        characters: Optional list of pre-selected characters to incorporate into the story
        provider: LLM provider to use (groq, openai, gpt4all). Defaults to groq.
        model: Model name to use (provider-specific)
        llm_client: Optional pre-configured LLM client
        
    Returns:
        StoryBook object with title and specified number of StoryBeat objects
    """
    if llm_client is None:
        llm_client = get_llm_client(provider=provider, model=model)
    
    # Language-specific instructions
    if language == "es":
        language_instruction = """CRITICAL: Write the entire storybook in Spanish (español). 
All text must be in Spanish:
- The title must be in Spanish
- The synopsis must be in Spanish
- The author_bio must be in Spanish
- All story text in each beat must be in Spanish
- Visual descriptions can be in Spanish (they will be translated to English for image generation)
- Sticker subjects should be in Spanish"""
        user_language_note = "IMPORTANTE: Escribe todo el cuento en español. El título, la sinopsis, la biografía del autor y todo el texto de la historia deben estar en español."
    else:
        language_instruction = """CRITICAL: Write the entire storybook in English.
All text must be in English:
- The title must be in English
- The synopsis must be in English
- The author_bio must be in English
- All story text in each beat must be in English
- Visual descriptions should be in English
- Sticker subjects should be in English"""
        user_language_note = "IMPORTANT: Write the entire storybook in English. The title, synopsis, author bio, and all story text in each beat must be in English."
    
    # Build character information for prompt if characters are provided
    character_info = ""
    if characters:
        logger.info(f"Incorporating {len(characters)} pre-selected character(s) into story generation")
        character_list = []
        for char in characters:
            # Truncate physical description if too long to prevent prompt bloat
            physical_desc = char.physical_description if char.physical_description else ""
            if len(physical_desc) > 200:
                physical_desc = physical_desc[:200] + "..."
            
            char_desc = f"- {char.name}"
            if char.species:
                char_desc += f" (a {char.species})"
            if physical_desc:
                char_desc += f": {physical_desc}"
            if char.key_features:
                # Limit key features to top 3 to keep prompt concise
                features_str = ', '.join(char.key_features[:3])
                char_desc += f" - Key features: {features_str}"
            character_list.append(char_desc)
        character_info = f"""

CRITICAL: You MUST incorporate the following pre-selected characters into your story. These characters MUST appear in the story and be central to the plot:

{chr(10).join(character_list)}

These characters are already created and must be used. Incorporate them naturally into the story based on the theme. Make sure these characters appear in multiple story beats and are important to the plot."""

    system_prompt = f"""You are an expert children's book author. Your task is to create a short, 
engaging storybook suitable for ages 4-8. 

{language_instruction}

CRITICAL: The story MUST be based on the theme provided by the user. Do not create your own unrelated story - the theme is the foundation and direction for the entire storybook.
{character_info}
Create exactly {num_pages} story beats. Each beat should:
- Have 2 paragraphs of engaging story text (age-appropriate)
- Include a visual_description that describes what should be shown visually
- List 1-3 sticker_subjects (specific objects/characters that will appear as stickers)

The story must be based on the provided theme and should be cohesive, with a clear beginning, middle, and end that all relate to and support the theme. Make it imaginative and fun while staying true to the theme!

You MUST return valid JSON matching this exact structure:
{{
    "title": "Story Title",
    "synopsis": "A brief 2-3 sentence summary of the story suitable for a back cover.",
    "author_bio": "A brief 2-3 sentence biography about the creator of this story, suitable for an 'About the Author' page.",
    "beats": [
        {{
            "text": "Paragraph 1...\\n\\nParagraph 2...",
            "visual_description": "Description of the visual scene",
            "sticker_subjects": ["subject1", "subject2"]
        }},
        ... (exactly {num_pages} beats total)
    ]
}}"""

    # Include character names in user prompt if characters are provided
    character_names_in_prompt = ""
    if characters and len(characters) > 0:
        char_names = ", ".join([char.name for char in characters])
        character_names_in_prompt = f"\n\nIMPORTANT: The following characters MUST appear in the story and be central to the plot: {char_names}. Make sure these characters are mentioned by name in the story text and appear in multiple story beats.\n"
    
    user_prompt = f"Create a children's storybook following this EXACT theme: {theme or 'adventure'}\n\nCRITICAL: The entire storybook must be based on and follow this theme. All story beats, characters, and plot elements must relate to and support this theme. Do not create an unrelated story.{character_names_in_prompt}\n\n{user_language_note}\n\nGenerate exactly {num_pages} story beats that tell a cohesive story based on the theme above.\n\nReturn only valid JSON, no additional text."

    try:
        logger.info(f"Generating storybook with theme: {theme}, pages: {num_pages}, language: {language}, characters: {len(characters) if characters else 0}")
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
        
        # Auto-fix beat count mismatch instead of failing
        if len(storybook.beats) != num_pages:
            if len(storybook.beats) > num_pages:
                # Too many beats: take first num_pages beats
                logger.warning(f"LLM generated {len(storybook.beats)} beats instead of {num_pages}. Trimming to first {num_pages} beats.")
                storybook.beats = storybook.beats[:num_pages]
            else:
                # Too few beats: this is more problematic, still fail but with better message
                raise ValueError(f"LLM generated only {len(storybook.beats)} story beats, but {num_pages} were requested. Cannot automatically fix insufficient beats.")
        
        return storybook
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating storybook: {e}")
