"""
Sticker Generator: Complete pipeline for generating stickers from image prompts.
Combines image generation, background removal, and storage.
"""

import os
import re
from typing import List, Optional, Tuple, Set
from src.models import ImagePrompt, Character, StoryBeat
from services.image_service import ImageService, get_image_service
from services.background_remover import process_image
from services.image_storage import ensure_job_directory, get_image_path
from services.character_service import match_character_to_subject, create_character_prompt_with_action
from dotenv import load_dotenv

load_dotenv()


async def generate_sticker(
    prompt: ImagePrompt,
    job_id: str,
    beat_num: int,
    image_service: Optional[ImageService] = None,
    bg_threshold: Optional[int] = None,
    autocrop_padding: Optional[int] = None,
    index: Optional[int] = None,
    seed: Optional[int] = None,
    character_description: Optional[str] = None
) -> str:
    """
    Generate a complete sticker from an image prompt.
    
    Pipeline:
    1. Generate image from prompt
    2. Remove white background
    3. Autocrop to content
    4. Save as PNG
    
    Args:
        prompt: ImagePrompt object with generation prompt and subject
        job_id: Unique job identifier
        beat_num: Story beat number (1-indexed)
        image_service: Optional pre-configured image service
        bg_threshold: Background removal threshold (default from env or 240)
        autocrop_padding: Padding for autocrop (default from env or 10)
        index: Optional index for duplicate subjects
        seed: Optional seed for image generation consistency (Pollinations)
        character_description: Optional character description for DALL-E consistency
        
    Returns:
        Path to saved sticker image
    """
    if image_service is None:
        provider = os.getenv("IMAGE_PROVIDER", "pollinations")
        image_service = get_image_service(provider=provider)
    
    if bg_threshold is None:
        bg_threshold = int(os.getenv("BG_REMOVAL_THRESHOLD", "240"))
    
    if autocrop_padding is None:
        autocrop_padding = int(os.getenv("AUTOCROP_PADDING", "10"))
    
    enable_border = os.getenv("ENABLE_STICKER_BORDER", "false").lower() == "true"
    
    raw_image_data = await image_service.generate_image(
        prompt=prompt.prompt,
        size="1024x1024",
        seed=seed,
        character_description=character_description
    )
    
    processed_image_data = process_image(
        raw_image_data,
        threshold=bg_threshold,
        padding=autocrop_padding,
        preserve_edges=True,
        add_border=enable_border
    )
    
    image_path = get_image_path(job_id, beat_num, prompt.subject, index=index)
    ensure_job_directory(job_id)
    
    with open(image_path, 'wb') as f:
        f.write(processed_image_data)
    
    from PIL import Image as PILImage
    with PILImage.open(image_path) as saved_img:
        if saved_img.mode != 'RGBA':
            rgba_img = saved_img.convert('RGBA')
            rgba_img.save(image_path, format='PNG', optimize=True)
    
    return str(image_path)


async def generate_background_image(
    prompt: ImagePrompt,
    job_id: str,
    beat_num: int,
    image_service: Optional[ImageService] = None
) -> str:
    """
    Generate a background image for a story beat.
    Background images are full-page scenes (not stickers, no background removal).
    
    Args:
        prompt: ImagePrompt object with background scene description
        job_id: Unique job identifier
        beat_num: Story beat number (1-indexed)
        image_service: Optional pre-configured image service
        
    Returns:
        Path to saved background image
    """
    if image_service is None:
        provider = os.getenv("IMAGE_PROVIDER", "pollinations")
        image_service = get_image_service(provider=provider)
    
    # Generate background image (no seed needed, backgrounds can vary)
    raw_image_data = await image_service.generate_image(
        prompt=prompt.prompt,
        size="1024x1024"
    )
    
    # Save background image (no background removal, keep as-is)
    assets_dir = ensure_job_directory(job_id)
    background_filename = f"beat_{beat_num}_background.png"
    background_path = assets_dir / background_filename
    
    with open(background_path, 'wb') as f:
        f.write(raw_image_data)
    
    from PIL import Image as PILImage
    with PILImage.open(background_path) as saved_img:
        if saved_img.mode != 'RGB':
            rgb_img = saved_img.convert('RGB')
            rgb_img.save(background_path, format='PNG', optimize=True)
    
    return str(background_path)


async def generate_stickers_for_beat(
    prompts: List[ImagePrompt],
    job_id: str,
    beat_num: int,
    beat: StoryBeat,
    image_service: Optional[ImageService] = None,
    bg_threshold: Optional[int] = None,
    autocrop_padding: Optional[int] = None,
    characters: Optional[List[Character]] = None,
    characters_appeared_before: Optional[Set[str]] = None
) -> Tuple[List[str], Set[str]]:
    """
    Generate all stickers for a story beat.
    Characters use base design + action context from story beat.
    
    Args:
        prompts: List of ImagePrompt objects for the beat
        job_id: Unique job identifier
        beat_num: Story beat number (1-indexed)
        beat: StoryBeat object for context
        image_service: Optional pre-configured image service
        bg_threshold: Background removal threshold
        autocrop_padding: Padding for autocrop
        characters: Optional list of characters for consistency matching
        characters_appeared_before: Optional set of character names that have appeared in previous beats
        
    Returns:
        Tuple of (list of paths to saved sticker images, set of character names that appeared in this beat)
    """
    image_paths = []
    
    subject_counts = {}
    for prompt in prompts:
        subject = prompt.subject
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    subject_indices = {}
    
    # Track which characters are in this beat
    beat_characters = []
    character_subjects = []
    generated_character_names = set()  # Track characters already generated in this beat
    
    for prompt in prompts:
        subject = prompt.subject
        
        if subject_counts[subject] > 1:
            if subject not in subject_indices:
                subject_indices[subject] = 0
            subject_indices[subject] += 1
            index = subject_indices[subject]
        else:
            index = None
        
        # Match character to subject
        matched_character = match_character_to_subject(subject, characters or [])
        
        if matched_character:
            # Skip if this character image was already generated in this beat
            if matched_character.name not in generated_character_names:
                beat_characters.append(matched_character)
                character_subjects.append((subject, matched_character))
                generated_character_names.add(matched_character.name)
            else:
                # Skip generating duplicate character image
                continue
        
        # Use character prompt with action context if character matched
        if matched_character:
            seed = matched_character.seed
            # Create prompt with base design + action context
            character_prompt_text = create_character_prompt_with_action(
                character=matched_character,
                story_context=beat.text,
                visual_description=beat.visual_description
            )
            
            # Ensure the prompt explicitly states single character and doesn't mention others
            # Remove any mentions of other characters
            character_name_lower = matched_character.name.lower()
            other_character_names = [char.name.lower() for char in (characters or []) 
                                   if char.name.lower() != character_name_lower]
            
            # Remove mentions of other characters
            for other_char in other_character_names:
                # Remove phrases like "with [other_char]", "and [other_char]", etc.
                character_prompt_text = re.sub(
                    r'\b(and|with|together|meeting)\s+' + re.escape(other_char) + r'\b',
                    '',
                    character_prompt_text,
                    flags=re.IGNORECASE
                )
            
            # Ensure "SINGLE character only" is prominent
            if 'SINGLE character only' not in character_prompt_text and 'ONE character only' not in character_prompt_text:
                character_prompt_text = f"SINGLE character only, {character_prompt_text}"
            
            # Clean up double spaces
            character_prompt_text = re.sub(r'\s+', ' ', character_prompt_text).strip()
            
            use_prompt = ImagePrompt(
                prompt=character_prompt_text,
                subject=prompt.subject
            )
            character_description = character_prompt_text  # For DALL-E consistency
        else:
            # Only generate stickers for non-character subjects if they're explicitly mentioned
            # in the story text (not just in subjects list)
            subject_lower = subject.lower()
            beat_text_lower = beat.text.lower()
            beat_visual_lower = beat.visual_description.lower()
            
            # Skip if subject doesn't appear in story context at all
            if subject_lower not in beat_text_lower and subject_lower not in beat_visual_lower:
                # Check if it's a common word that might match partially
                subject_words = subject_lower.split()
                if not any(word in beat_text_lower or word in beat_visual_lower for word in subject_words if len(word) > 3):
                    continue  # Skip this subject - it doesn't fit the story
            
            use_prompt = prompt
            seed = None
            character_description = None
        
        path = await generate_sticker(
            prompt=use_prompt,
            job_id=job_id,
            beat_num=beat_num,
            image_service=image_service,
            bg_threshold=bg_threshold,
            autocrop_padding=autocrop_padding,
            index=index,
            seed=seed,
            character_description=character_description
        )
        image_paths.append(path)
    
    # Track unique characters that appeared in this beat (for tracking across beats)
    # Use dict to track unique characters by name (Character objects aren't hashable)
    unique_characters_dict = {char.name: char for char in beat_characters}
    unique_characters = list(unique_characters_dict.values())
    
    # Return image paths and set of characters that appeared in this beat
    characters_appeared_in_beat = {char.name for char in unique_characters}
    return image_paths, characters_appeared_in_beat
