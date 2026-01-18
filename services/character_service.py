"""
Character Service: Extracts and manages character consistency for storybooks.
"""

import json
import hashlib
import re
from pathlib import Path
from typing import List, Optional, Tuple, Set
from services.llm_client import LLMClient, get_llm_client
from services.image_service import ImageService, get_image_service
from services.image_storage import ensure_job_directory, save_image
from services.background_remover import process_image
from src.models import StoryBook, Character, StoryBeat


def create_refined_character_prompt(character: Character) -> str:
    """
    Create a refined, highly detailed prompt for consistent character image generation.
    This prompt is used as the base design for characters.
    
    Args:
        character: Character object with detailed description
        
    Returns:
        Refined, detailed prompt string for character base design
    """
    prompt_parts = []
    
    # Character name and species
    if character.species:
        prompt_parts.append(f"{character.name}, a {character.species}")
    else:
        prompt_parts.append(character.name)
    
    # Detailed physical description
    prompt_parts.append(character.physical_description)
    
    # Key features
    if character.key_features:
        features_str = ", ".join(character.key_features)
        prompt_parts.append(f"Distinctive features: {features_str}")
    
    # Color palette - use specific colors
    if character.color_palette:
        color_descriptions = []
        for key, value in character.color_palette.items():
            if value:
                key_display = key.replace('_', ' ').title()
                color_descriptions.append(f"{key_display}: {value}")
        if color_descriptions:
            prompt_parts.append(f"Color scheme: {', '.join(color_descriptions)}")
    
    # Art style specifications for consistency (base design only, no pose/action)
    prompt_parts.append("3D rendered sticker-style character design")
    prompt_parts.append("Children's book illustration style, cute and friendly")
    
    return ", ".join(prompt_parts)


def extract_emotion_from_context(story_context: str, visual_description: str) -> str:
    """Extract emotion from story context and visual description."""
    # Conservative keyword-based extraction - only match explicit emotion words
    # Order matters: check more specific emotions first to avoid false positives
    emotions_map = {
        # Happy emotions (check first for positive contexts)
        'happy': ['happy', 'joyful', 'cheerful', 'smiling', 'delighted', 'excited', 'laughing', 'grinning', 'gleeful', 'merry', 'pleased', 'glad'],
        # Scared emotions (specific fear words)
        'scared': ['scared', 'afraid', 'frightened', 'terrified', 'panicked', 'alarmed'],
        # Sad emotions
        'sad': ['sad', 'unhappy', 'crying', 'tears', 'disappointed', 'upset', 'sobbing', 'weeping', 'melancholy', 'heartbroken', 'sorrowful'],
        # Angry emotions (be more specific to avoid matching "mad" in "mad at")
        'angry': ['angry', 'furious', 'annoyed', 'frustrated', 'irritated', 'enraged', 'outraged'],
        # Surprised emotions
        'surprised': ['surprised', 'shocked', 'amazed', 'astonished', 'startled', 'stunned'],
        # Confused (remove "bewildered" as it conflicts with surprised)
        'confused': ['confused', 'puzzled', 'perplexed', 'mystified'],
        # Proud emotions
        'proud': ['proud', 'triumphant', 'confident'],
        # Curious
        'curious': ['curious', 'inquisitive', 'interested', 'intrigued']
    }
    
    # Combine context for better matching
    text = (story_context + " " + visual_description).lower()
    
    # Check for explicit emotion keywords only - be conservative
    # Use word boundaries to avoid partial matches
    for emotion, keywords in emotions_map.items():
        for keyword in keywords:
            # Match whole words only (word boundaries)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return emotion
    
    # Only use context clues if emotion is very clear
    # Check for very specific negative contexts that strongly suggest emotion
    very_negative_indicators = ['crying', 'sobbing', 'tears streaming', 'defeated', 'heartbroken']
    if any(indicator in text for indicator in very_negative_indicators):
        return 'sad'
    
    very_fear_indicators = ['terrified', 'panic', 'fear gripping', 'shaking with fear']
    if any(indicator in text for indicator in very_fear_indicators):
        return 'scared'
    
    very_positive_indicators = ['celebrating', 'jumping for joy', 'bursting with happiness']
    if any(indicator in text for indicator in very_positive_indicators):
        return 'happy'
    
    return "neutral"  # Default emotion - default to neutral instead of assuming


def create_character_prompt_with_action(
    character: Character,
    story_context: str,
    visual_description: str,
    pose_action: Optional[str] = None
) -> str:
    """
    Create a character prompt with base design + emotion + action/pose context from story.
    Ensures single character only with explicit emotion expression.
    
    Args:
        character: Character object with base design
        story_context: Story text for context
        visual_description: Visual description from beat
        pose_action: Optional specific pose/action to add
        
    Returns:
        Character prompt with base design + emotion + action context, single character only
    """
    base_prompt = get_character_refined_prompt(character)
    
    # Extract emotion from context
    emotion = extract_emotion_from_context(story_context, visual_description)
    
    # Create detailed emotion description with specific facial expressions
    emotion_details = {
        'happy': 'with a big wide smile, bright eyes, cheerful expression, joyful facial features',
        'sad': 'with a downturned mouth, teary eyes, sad expression, drooping facial features',
        'angry': 'with a furrowed brow, narrowed eyes, angry expression, frowning mouth',
        'scared': 'with wide eyes showing fear, open mouth, scared expression, worried facial features',
        'surprised': 'with wide-open eyes, raised eyebrows, surprised expression, open mouth',
        'confused': 'with raised eyebrows, tilted head, puzzled expression, questioning look',
        'proud': 'with a confident smile, lifted head, proud expression, determined eyes',
        'skeptical': 'with narrowed eyes, raised eyebrow, skeptical expression, questioning look',
        'curious': 'with bright interested eyes, slightly tilted head, curious expression, attentive look',
        'neutral': 'with a friendly neutral expression, kind eyes, gentle smile'
    }
    
    emotion_text = emotion_details.get(emotion, emotion_details['neutral'])
    
    # Extract action/pose
    action_context = pose_action if pose_action else visual_description
    
    # Combine: SINGLE character + emotion (prominent) + base design + action
    # Put emotion first and repeat it for emphasis
    prompt = f"SINGLE character only, {emotion_text}, {emotion} emotion clearly visible in facial expression, {base_prompt}, {action_context}, clean white background, professional studio lighting, soft shadows, high detail, crisp edges, vibrant colors, sticker-style, consistent character design matching the base, emphasis on {emotion} facial expression"
    
    return prompt


def create_character_interaction_prompt(
    characters: List[Character],
    story_context: str,
    visual_description: str
) -> str:
    """
    Create a prompt for character interaction image (multiple characters together).
    
    Args:
        characters: List of characters (should be 2)
        story_context: Story text for context
        visual_description: Visual description from beat
        
    Returns:
        Interaction prompt string
    """
    if len(characters) < 2:
        raise ValueError("Need at least 2 characters for interaction")
    
    char1, char2 = characters[0], characters[1]
    char1_base = get_character_refined_prompt(char1)
    char2_base = get_character_refined_prompt(char2)
    
    # Create interaction prompt
    prompt = f"Sticker-style character interaction: {char1.name} and {char2.name} together, {char1_base}, {char2_base}, {visual_description}, showing their interaction and relative positions, clean white background, professional studio lighting, 3D rendered, children's book illustration style, cute and friendly, high detail, crisp edges, vibrant colors"
    
    return prompt


async def extract_main_characters(
    theme: str,
    storybook: StoryBook,
    language: str = "en",
    llm_client: Optional[LLMClient] = None
) -> List[Character]:
    """
    Extract main characters from a generated storybook.
    Uses LLM to identify all main/important characters and generate detailed physical descriptions.
    
    Args:
        theme: The original theme for the storybook
        storybook: The generated StoryBook to extract characters from
        language: Language of the storybook ("en" for English, "es" for Spanish, default: "en")
        llm_client: Optional pre-configured LLM client
        
    Returns:
        List of Character objects with physical descriptions
    """
    if llm_client is None:
        llm_client = get_llm_client()
    
    # Combine story text for context
    story_text = "\n\n".join([beat.text for beat in storybook.beats])
    
    # Language-specific instructions
    if language == "es":
        language_note = """IMPORTANT: The story is written in Spanish (español). 
Analyze the Spanish story and provide character descriptions. Character names should be preserved as they appear in the Spanish story.
Physical descriptions should be detailed and can reference the Spanish context, but use clear, specific color names in English for consistency."""
        analysis_instruction = "Analyze the following Spanish children's story"
    else:
        language_note = ""
        analysis_instruction = "Analyze the following children's story"
    
    system_prompt = f"""You are an expert character designer and visual artist specializing in children's book illustration.
Your task is to identify ALL main/important characters from a story and create EXTREMELY DETAILED physical and visual descriptions for each character that will ensure perfect visual consistency across all images.

{language_note}

Identify all characters that are:
- Main protagonists or important characters
- Appear multiple times in the story
- Central to the story's plot

For each character, you MUST provide:
- Character name
- Species/type (if applicable: human, mouse, bear, rabbit, cat, dog, etc.)
- EXTREMELY DETAILED physical description including:
  * Exact size and proportions
  * Specific colors (use precise color names like "emerald green", "sapphire blue", not just "green" or "blue")
  * Distinctive facial features, expressions, and characteristics
  * Body shape and posture
  * Texture and surface details (smooth, fuzzy, scaly, etc.)
  * Any accessories, clothing, or unique markings
  * Eye shape, size, and color
  * Overall art style description (cute, realistic, cartoonish, etc.)
- Key visual features that make this character INSTANTLY recognizable
- Comprehensive color palette with SPECIFIC color names

The descriptions must be so detailed that an artist could recreate the EXACT same character design from scratch multiple times with perfect consistency.

You MUST return valid JSON matching this exact structure:
{{
    "characters": [
        {{
            "name": "Character Name",
            "species": "human/mouse/etc or null",
            "physical_description": "EXTREMELY detailed description including size, colors, features, textures, style",
            "key_features": ["distinctive feature 1", "distinctive feature 2", "distinctive feature 3"],
            "color_palette": {{
                "hair_color": "specific color name or null",
                "eye_color": "specific color name or null",
                "skin_color": "specific color name or null",
                "clothing_color": "specific color name or null",
                "primary_color": "specific color name or null",
                "accent_color": "specific color name or null"
            }}
        }},
        ... (one for each main character)
    ]
}}"""

    user_prompt = f"""{analysis_instruction} and identify ALL main/important characters.

Theme: {theme}
Title: {storybook.title}

Story:
{story_text}

Identify all main characters (protagonists and important recurring characters) and provide EXTREMELY DETAILED physical and visual descriptions that will ensure perfect visual consistency across all images. Include specific colors, sizes, textures, and distinctive features that make each character instantly recognizable.

Return only valid JSON, no additional text."""

    try:
        content = await llm_client.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5  # Lower temperature for more consistent descriptions
        )
        
        content = content.strip()
        if content.endswith('</s>'):
            content = content[:-4].strip()
        
        try:
            character_data = json.loads(content)
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
                    character_data = json.loads(json_content)
                else:
                    raise
            else:
                raise
        
        # Extract all characters
        characters = []
        characters_list = character_data.get("characters", [])
        
        if not isinstance(characters_list, list):
            return []
        
        for char_data in characters_list:
            character = Character(
                name=char_data.get("name", "Unknown"),
                species=char_data.get("species"),
                physical_description=char_data.get("physical_description", ""),
                key_features=char_data.get("key_features", []),
                color_palette=char_data.get("color_palette")
            )
            
            # Create and store refined prompt (base design only)
            character.refined_prompt = create_refined_character_prompt(character)
            
            characters.append(character)
        
        return characters
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error extracting characters: {e}")


# Keep the old function for backward compatibility, but mark as deprecated
async def extract_protagonist_from_story(
    theme: str,
    storybook: StoryBook,
    llm_client: Optional[LLMClient] = None
) -> Optional[Character]:
    """
    Extract the protagonist character from a generated storybook.
    DEPRECATED: Use extract_main_characters() instead for multi-character support.
    
    Returns the first character from extract_main_characters() for backward compatibility.
    """
    characters = await extract_main_characters(theme, storybook, llm_client=llm_client)
    return characters[0] if characters else None


def generate_character_reference(character: Character) -> str:
    """
    Format a Character object into a reference string for use in image prompts.
    
    Args:
        character: Character object to format
        
    Returns:
        Formatted character reference string for image prompts
    """
    reference_parts = [f"Character: {character.name}"]
    
    if character.species:
        reference_parts.append(f"Species: {character.species}")
    
    reference_parts.append(f"Physical Description: {character.physical_description}")
    
    if character.key_features:
        features_str = ", ".join(character.key_features)
        reference_parts.append(f"Key Features: {features_str}")
    
    if character.color_palette:
        color_items = []
        for key, value in character.color_palette.items():
            if value:
                color_items.append(f"{key.replace('_', ' ').title()}: {value}")
        if color_items:
            reference_parts.append(f"Colors: {', '.join(color_items)}")
    
    return ". ".join(reference_parts) + ". "


def generate_characters_reference(characters: List[Character]) -> str:
    """
    Format multiple Character objects into a combined reference string for use in image prompts.
    
    Args:
        characters: List of Character objects to format
        
    Returns:
        Formatted character reference string with all characters
    """
    if not characters:
        return ""
    
    references = []
    for character in characters:
        references.append(generate_character_reference(character))
    
    return "\n\n".join(references)


def generate_concise_character_reference(character: Character) -> str:
    """
    Generate a concise character reference focusing on essential species and key features.
    Used when prompt length is a concern (e.g., GPT4All with 2048 token limit).
    
    Args:
        character: Character object to format
        
    Returns:
        Concise character reference string
    """
    parts = [f"{character.name}"]
    
    # Always include species - this is critical
    if character.species:
        parts.append(f"({character.species})")
    
    # Include only top 2 key features
    if character.key_features:
        parts.append(f"Features: {', '.join(character.key_features[:2])}")
    
    # Include primary color only
    if character.color_palette:
        primary = (character.color_palette.get("primary_color") or 
                  character.color_palette.get("skin_color") or 
                  character.color_palette.get("hair_color"))
        if primary:
            parts.append(f"Color: {primary}")
    
    return " - ".join(parts)


def generate_concise_characters_reference(characters: List[Character]) -> str:
    """
    Generate concise character references for all characters.
    Used when prompt length is a concern.
    
    Args:
        characters: List of Character objects to format
        
    Returns:
        Concise character reference string with all characters
    """
    if not characters:
        return ""
    
    references = []
    for character in characters:
        references.append(generate_concise_character_reference(character))
    
    return ". ".join(references) + "."


async def generate_character_reference_image(
    character: Character,
    job_id: str,
    image_service: Optional[ImageService] = None
) -> Tuple[str, int]:
    """
    Generate an anchor reference image for the character (concept art, front view).
    This image serves as the base design reference for maintaining consistency.
    Uses the refined prompt for the base design (front view, neutral pose).
    
    Args:
        character: Character object to generate reference image for
        job_id: Unique job identifier
        image_service: Optional pre-configured image service
        
    Returns:
        Tuple of (reference_image_path, seed) where seed is deterministic hash
    """
    if image_service is None:
        image_service = get_image_service()
    
    # Type assertion: get_image_service always returns a non-None ImageService
    assert image_service is not None, "get_image_service should always return a valid ImageService"
    
    # Generate deterministic seed from character name (hash)
    seed = int(hashlib.md5(character.name.encode()).hexdigest()[:8], 16) % (2**31)
    
    # Use refined prompt for reference image (front view, base design only)
    if character.refined_prompt:
        reference_prompt = f"{character.refined_prompt}, front view, character concept art, detailed character design sheet, neutral pose, clean white background, professional studio lighting"
    else:
        # Fallback to basic prompt if refined_prompt not available
        reference_prompt = f"{character.name} concept art, front view, clean white background, detailed character design"
        if character.species:
            reference_prompt += f", {character.species}"
        reference_prompt += f", {character.physical_description}"
        if character.key_features:
            features_str = ", ".join(character.key_features)
            reference_prompt += f", {features_str}"
        reference_prompt += ", sticker-style, children's book illustration, professional lighting"
    
    try:
        # Generate reference image with seed for consistency
        raw_image_data = await image_service.generate_image(
            prompt=reference_prompt,
            size="1024x1024",
            seed=seed
        )
        
        # Process image (background removal, autocrop)
        processed_image_data = process_image(
            raw_image_data,
            threshold=240,
            padding=10,
            preserve_edges=True,
            add_border=False
        )
        
        # Save reference image
        assets_dir = ensure_job_directory(job_id)
        safe_name = "".join(c for c in character.name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        reference_filename = f"character_reference_{safe_name}.png"
        reference_path = assets_dir / reference_filename
        
        image_path = save_image(reference_path, processed_image_data)
        
        # Ensure RGBA mode
        from PIL import Image as PILImage
        with PILImage.open(image_path) as saved_img:
            if saved_img.mode != 'RGBA':
                rgba_img = saved_img.convert('RGBA')
                rgba_img.save(image_path, format='PNG', optimize=True)
        
        return (str(image_path), seed)
        
    except Exception as e:
        raise RuntimeError(f"Error generating character reference image: {e}")


def match_character_to_subject(subject: str, characters: List[Character]) -> Optional[Character]:
    """
    Match a sticker subject to a character based on name/species similarity.
    
    Args:
        subject: The sticker subject (e.g., "frog", "scorpion", "the frog")
        characters: List of Character objects to match against
        
    Returns:
        Matching Character object, or None if no match found
    """
    if not characters:
        return None
    
    subject_lower = subject.lower().strip()
    # Remove common articles and descriptors
    subject_clean = subject_lower.replace("the ", "").replace("a ", "").replace("an ", "").strip()
    
    for character in characters:
        # Match by character name
        char_name_lower = character.name.lower().strip()
        if char_name_lower in subject_clean or subject_clean in char_name_lower:
            return character
        
        # Match by species
        if character.species:
            species_lower = character.species.lower().strip()
            if species_lower in subject_clean or subject_clean in species_lower:
                return character
        
        # Match by name parts
        name_parts = char_name_lower.split()
        for part in name_parts:
            if part in subject_clean and len(part) > 2:  # Only match if part is meaningful
                return character
    
    return None


def match_characters_by_similarity(extracted_char: Character, stored_chars: List[Character]) -> Optional[Character]:
    """
    Match an extracted character with stored characters based on species, description, and key features similarity.
    Used to avoid duplicate character generation when a stored character matches an extracted one.
    
    Args:
        extracted_char: Character extracted from the story
        stored_chars: List of stored Character objects to match against
        
    Returns:
        Best matching stored Character object, or None if no good match found
    """
    if not stored_chars:
        return None
    
    best_match = None
    best_score = 0.0
    
    extracted_species_lower = extracted_char.species.lower() if extracted_char.species else None
    extracted_desc_lower = extracted_char.physical_description.lower() if extracted_char.physical_description else ""
    extracted_features = set(f.lower() for f in extracted_char.key_features) if extracted_char.key_features else set()
    extracted_name_lower = extracted_char.name.lower()
    
    # Extract keywords from description (simple word-based approach)
    # Remove common stop words and get meaningful keywords
    stop_words = {"the", "a", "an", "is", "are", "with", "and", "or", "but", "has", "have", "had", "was", "were", "be", "been", "being"}
    extracted_desc_words = set(
        word.lower() 
        for word in re.findall(r'\b\w+\b', extracted_desc_lower) 
        if len(word) > 3 and word.lower() not in stop_words
    )
    
    for stored_char in stored_chars:
        score = 0.0
        
        stored_species_lower = stored_char.species.lower() if stored_char.species else None
        stored_desc_lower = stored_char.physical_description.lower() if stored_char.physical_description else ""
        stored_features = set(f.lower() for f in stored_char.key_features) if stored_char.key_features else set()
        stored_name_lower = stored_char.name.lower()
        
        # 1. Species match (highest priority - 40 points)
        if extracted_species_lower and stored_species_lower:
            if extracted_species_lower == stored_species_lower:
                score += 40.0
            elif extracted_species_lower in stored_species_lower or stored_species_lower in extracted_species_lower:
                score += 30.0
        
        # 2. Name similarity (30 points if similar)
        if extracted_name_lower == stored_name_lower:
            score += 30.0
        elif extracted_name_lower in stored_name_lower or stored_name_lower in extracted_name_lower:
            score += 15.0
        
        # 3. Key features overlap (20 points)
        if extracted_features and stored_features:
            overlap = len(extracted_features & stored_features)
            total = len(extracted_features | stored_features)
            if total > 0:
                feature_similarity = overlap / total
                score += 20.0 * feature_similarity
        
        # 4. Description keyword overlap (10 points)
        if extracted_desc_words:
            stored_desc_words = set(
                word.lower() 
                for word in re.findall(r'\b\w+\b', stored_desc_lower) 
                if len(word) > 3 and word.lower() not in stop_words
            )
            if stored_desc_words:
                overlap = len(extracted_desc_words & stored_desc_words)
                total = len(extracted_desc_words | stored_desc_words)
                if total > 0:
                    desc_similarity = overlap / total
                    score += 10.0 * desc_similarity
        
        # Track best match
        if score > best_score:
            best_score = score
            best_match = stored_char
    
    # Only return match if similarity score is high enough (threshold: 40 = species match or strong name match)
    if best_score >= 40.0:
        return best_match
    
    return None


def get_character_refined_prompt(character: Character) -> str:
    """
    Get the refined prompt for a character. Creates it if it doesn't exist.
    This is the BASE design prompt (no pose/action).
    
    Args:
        character: Character object
        
    Returns:
        Refined base prompt string
    """
    if character.refined_prompt:
        return character.refined_prompt
    else:
        # Generate refined prompt if not already stored
        return create_refined_character_prompt(character)


def ensure_characters_in_beats(storybook: StoryBook, characters: List[Character], selected_character_names: Optional[Set[str]] = None) -> None:
    """
    Ensure main characters appear in sticker_subjects when mentioned in story text.
    Updates beats in place to add missing main characters to sticker_subjects.
    
    Selected characters (those in selected_character_names) will always appear in at least the first beat,
    even if not mentioned in the story text.
    
    Args:
        storybook: StoryBook object to update
        characters: List of main characters
        selected_character_names: Optional set of selected character names (lowercase) that should always appear
    """
    if not characters:
        return
    
    # Normalize selected character names to lowercase
    selected_names_lower = set(name.lower() for name in selected_character_names) if selected_character_names else set()
    
    # Create lookup dictionaries for character names and species
    char_names_lower = {char.name.lower(): char for char in characters}
    char_species_lower = {}
    for char in characters:
        if char.species:
            char_species_lower[char.species.lower()] = char
    
    for beat_idx, beat in enumerate(storybook.beats):
        beat_text_lower = beat.text.lower()
        existing_subjects_lower = [s.lower() for s in beat.sticker_subjects]
        
        # Check each character
        for character in characters:
            char_name_lower = character.name.lower()
            char_species_lower_val = character.species.lower() if character.species else None
            is_selected = char_name_lower in selected_names_lower
            
            # Check if character is mentioned in text
            mentioned = False
            # Check by name
            if char_name_lower in beat_text_lower:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(char_name_lower) + r'\b'
                if re.search(pattern, beat_text_lower):
                    mentioned = True
            # Check by species if name not found
            elif char_species_lower_val and char_species_lower_val in beat_text_lower:
                pattern = r'\b' + re.escape(char_species_lower_val) + r'\b'
                if re.search(pattern, beat_text_lower):
                    mentioned = True
            
            # Selected characters should appear in first beat even if not mentioned
            # or if mentioned in any beat, include them
            should_include = mentioned or (is_selected and beat_idx == 0)
            
            if should_include:
                # Check if already in subjects (by name or species)
                already_included = False
                for subject in beat.sticker_subjects:
                    subject_lower = subject.lower()
                    if char_name_lower in subject_lower or subject_lower in char_name_lower:
                        already_included = True
                        break
                    if char_species_lower_val and (char_species_lower_val in subject_lower or subject_lower in char_species_lower_val):
                        already_included = True
                        break
                
                # Add character if not already included
                if not already_included:
                    # Prefer character name, fallback to species
                    subject_to_add = character.name
                    if char_species_lower_val and character.species:
                        # If species is more descriptive, use it (e.g., "frog" vs "Freddy")
                        if len(char_species_lower_val) < len(char_name_lower) or char_species_lower_val in existing_subjects_lower:
                            subject_to_add = character.species
                    
                    beat.sticker_subjects.append(subject_to_add)
