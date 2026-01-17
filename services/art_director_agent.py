"""
Art Director Agent: Converts story beats into technical image generation prompts.
Handles character variations, interactions, and background images.
"""

import json
import re
import logging
from typing import List, Optional, Tuple, Dict
from services.llm_client import get_llm_client, LLMClient
from src.models import StoryBeat, ImagePrompt, Character

logger = logging.getLogger(__name__)

# Art Direction Style Templates
# Each style defines keywords that will be appended to all image prompts for visual consistency
ART_STYLES = {
    "CLAYMATION": {
        "name": "Claymation",
        "keywords": "stop-motion, plasticine texture, studio lighting, soft shadows, clay animation style"
    },
    "VINTAGE_SKETCH": {
        "name": "Vintage Sketch",
        "keywords": "vintage illustration, hand-drawn sketch style, ink and watercolor, classic children's book art"
    },
    "FLAT_DESIGN": {
        "name": "Flat Design",
        "keywords": "flat design, minimalist, bold colors, clean geometric shapes, modern illustration"
    },
    "3D_RENDERED": {
        "name": "3D Rendered",
        "keywords": "3D rendered, photorealistic lighting, soft shadows, professional studio quality"
    },
    "WATERCOLOR": {
        "name": "Watercolor",
        "keywords": "watercolor painting, soft brush strokes, translucent colors, artistic illustration"
    },
    "LINE_ART": {
        "name": "Line Art",
        "keywords": "line art illustration, bold black outlines, simple coloring, cartoon style"
    }
}

# Default style (matches current behavior)
DEFAULT_STYLE = "3D_RENDERED"


def get_style_keywords(style_name: Optional[str] = None) -> str:
    """
    Get style keywords for a given style name.
    
    Args:
        style_name: Style name (case-insensitive). If None or invalid, returns default style keywords.
        
    Returns:
        String of comma-separated style keywords
    """
    if style_name is None:
        style_name = DEFAULT_STYLE
    else:
        style_name = style_name.upper().strip()
    
    style_info = ART_STYLES.get(style_name)
    if style_info is None:
        logger.warning(f"Unknown style '{style_name}', falling back to default style '{DEFAULT_STYLE}'")
        style_info = ART_STYLES[DEFAULT_STYLE]
    
    return style_info["keywords"]


def apply_style_to_prompt(prompt: str, style_name: Optional[str] = None) -> str:
    """
    Append style keywords to a prompt string.
    Style keywords are appended at the end to avoid interfering with character descriptions.
    
    Args:
        prompt: The prompt text to enhance
        style_name: Style name (case-insensitive). If None, uses default style.
        
    Returns:
        Prompt string with style keywords appended
    """
    style_keywords = get_style_keywords(style_name)
    
    # Append style keywords at the end, separated by comma
    if prompt.strip():
        # Remove trailing comma/period if present
        prompt = prompt.rstrip('., ')
        return f"{prompt}, {style_keywords}"
    else:
        return style_keywords


def enhance_background_prompt_with_characters(
    prompt: str,
    beat: StoryBeat,
    characters: List[Character]
) -> str:
    """
    Enhance a background prompt to explicitly include character species and features.
    This ensures characters appear correctly in full-page scenes (e.g., frogs stay as frogs, not humans).
    
    Args:
        prompt: The background prompt text
        beat: StoryBeat for context
        characters: List of characters that might appear in the scene
        
    Returns:
        Enhanced prompt with explicit character species and features
    """
    if not characters:
        return prompt
    
    # Check which characters are mentioned in the beat
    beat_text_lower = beat.text.lower()
    beat_visual_lower = beat.visual_description.lower()
    mentioned_characters = []
    
    for char in characters:
        char_name_lower = char.name.lower()
        char_species_lower = char.species.lower() if char.species else None
        
        # Check if character is mentioned in beat
        if (char_name_lower in beat_text_lower or char_name_lower in beat_visual_lower or
            (char_species_lower and (char_species_lower in beat_text_lower or char_species_lower in beat_visual_lower))):
            mentioned_characters.append(char)
    
    if not mentioned_characters:
        return prompt
    
    # Build character descriptions with explicit species
    character_descriptions = []
    for char in mentioned_characters:
        char_desc_parts = []
        
        # Always include species explicitly
        if char.species:
            char_desc_parts.append(f"{char.name} is a {char.species}")
        else:
            char_desc_parts.append(f"{char.name}")
        
        # Add key physical features
        if char.key_features:
            features_str = ", ".join(char.key_features[:3])  # Limit to top 3 features
            char_desc_parts.append(f"with {features_str}")
        
        # Add color information if available
        if char.color_palette:
            primary_color = char.color_palette.get("primary_color") or char.color_palette.get("skin_color") or char.color_palette.get("hair_color")
            if primary_color:
                char_desc_parts.append(f"{primary_color} colored")
        
        char_description = " ".join(char_desc_parts)
        character_descriptions.append(char_description)
    
    # Enhance the prompt
    if character_descriptions:
        # Check if prompt already mentions character species
        prompt_lower = prompt.lower()
        has_species_mention = any(
            (char.species and char.species.lower() in prompt_lower) 
            for char in mentioned_characters
        )
        
        if not has_species_mention:
            # Add character descriptions to the prompt
            char_info = ". ".join(character_descriptions)
            enhanced_prompt = f"{prompt}. IMPORTANT: Characters in scene - {char_info}. Characters must appear with their correct species and features as described."
            return enhanced_prompt
        else:
            # Species is mentioned, but add reinforcement
            char_info = ". ".join(character_descriptions)
            enhanced_prompt = f"{prompt}. Character details: {char_info}. Ensure characters maintain their species type (a mouse stays a mouse, a bear stays a bear, etc.)"
            return enhanced_prompt
    
    return prompt


def clean_prompt_for_single_character(prompt: str, character_name: Optional[str] = None) -> str:
    """
    Clean a prompt to ensure it only mentions ONE character.
    Removes mentions of multiple characters, interactions, etc.
    
    Args:
        prompt: The prompt text to clean
        character_name: Optional character name to keep, remove others
        
    Returns:
        Cleaned prompt text with only single character references
    """
    prompt_lower = prompt.lower()
    
    # Patterns that indicate multiple characters
    multi_character_patterns = [
        r'\b(and|with|together|meeting|interaction|interacting)\s+\w+',
        r'\b(characters|two|both|them|they)\s',
        r'\b(the\s+\w+\s+and\s+the\s+\w+)',
        r'\b(\w+\s+and\s+\w+)\s+(together|meeting)',
        r'\b(interaction|together|meeting|greeting)',
    ]
    
    # Remove multi-character phrases
    cleaned = prompt
    for pattern in multi_character_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Ensure "SINGLE character only" or "ONE character only" is present
    if 'single character only' not in cleaned.lower() and 'one character only' not in cleaned.lower():
        # Add it at the beginning
        cleaned = f"SINGLE character only, {cleaned}"
    
    # Remove duplicate words and clean up spacing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove trailing commas
    cleaned = cleaned.rstrip(',')
    
    return cleaned


async def generate_image_prompts(
    beat: StoryBeat,
    character_reference: Optional[str] = None,
    character_reference_image_path: Optional[str] = None,
    characters: Optional[List[Character]] = None,
    style: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    llm_client: Optional[LLMClient] = None
) -> Tuple[List[ImagePrompt], Optional[ImagePrompt]]:
    """
    Convert a story beat into technical 3D-modeling prompts for image generation.
    Generates prompts for stickers and a background image.
    
    Args:
        beat: The StoryBeat to convert into image prompts
        character_reference: Optional character reference string for consistency
        character_reference_image_path: Optional path to character reference image
        characters: Optional list of characters for interaction detection
        style: Optional art style name (CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART)
        provider: LLM provider to use (groq, openai, gpt4all). Defaults to groq.
        model: Model name to use (provider-specific)
        llm_client: Optional pre-configured LLM client
        
    Returns:
        Tuple of (List of ImagePrompt objects for stickers, Optional background ImagePrompt)
    """
    if llm_client is None:
        llm_client = get_llm_client(provider=provider, model=model)
    
    # Detect character interactions (multiple characters in beat)
    character_subjects = []
    if characters:
        for char in characters:
            char_name_lower = char.name.lower()
            char_species_lower = char.species.lower() if char.species else None
            for subject in beat.sticker_subjects:
                subject_lower = subject.lower()
                if (char_name_lower in subject_lower or subject_lower in char_name_lower or
                    (char_species_lower and (char_species_lower in subject_lower or subject_lower in char_species_lower))):
                    character_subjects.append((subject, char))
    
    # Check if we have multiple characters (potential interaction)
    # Use dict to track unique characters by name (Character objects aren't hashable)
    unique_characters_dict = {char.name: char for _, char in character_subjects}
    unique_characters = list(unique_characters_dict.values())
    has_character_interaction = len(unique_characters) >= 2
    
    system_prompt = """You are an expert art director specializing in 3D modeling and rendering. 
Your task is to create technical, detailed prompts for generating "sticker-style" images.

Each image should be:
- Sticker-style with clean, bold outlines
- 3D rendered or illustrated
- Suitable for transparent background (PNG)
- Bright, colorful, and child-friendly
- Detailed enough for a professional 3D modeler to understand

Note: Art style keywords will be automatically applied to all prompts for visual consistency across the book.
Focus on describing the content, poses, emotions, and actions - the artistic style will be added programmatically.

IMPORTANT: The story text you receive may be in Spanish, but you MUST generate all image prompts in English. English prompts work better with image generation AI models, so translate any Spanish story content to English when creating image prompts.

For character images:
- CRITICAL: Each character sticker must show EXACTLY ONE SINGLE character - NEVER include multiple characters, interactions, or other characters in the same image
- Use the character's base design (colors, features, appearance) from the reference
- Add specific poses, actions, and expressions based on the story context
- Focus on showing character emotions and expressions (happy, sad, surprised, scared, etc.) based on the story context
- Characters should vary in pose/action and emotion across different beats while maintaining visual consistency
- DO NOT mention other characters, interactions, or multiple characters in character sticker prompts

For background images (CRITICAL - these become full-page illustrations):
- Create a COMPLETE full-page scene that tells the story visually
- Should be a complete, detailed illustration suitable for a full page in a children's book
- Include all relevant characters, objects, and environmental elements from the story beat
- The scene should be rich, detailed, and visually engaging - it will fill the entire page
- Describe the complete scene composition, including foreground, middle ground, and background elements
- Should be appropriate for children's book illustration style
- The image will be used as a full-page background with text overlaid, so ensure important visual elements don't conflict with text placement areas
- CRITICAL: When characters appear in the scene, you MUST explicitly mention their SPECIES (human, animal type, etc.) and key physical features
- Characters in the background scene MUST match their species and appearance from the character reference - do NOT change character species (if a character is described as a mouse, keep it as a mouse, not a human, etc.)
- Always specify the character's species type clearly (e.g., "a small brown mouse character", "a young human character", "a friendly bear character")

CRITICAL CONSISTENCY REQUIREMENTS:
- Characters MUST maintain the same design (colors, features, appearance) as the reference
- But characters should have DIFFERENT poses/actions/expressions based on the story context
- Character images must match the base design exactly but vary in pose/action

The prompts should be technical but clear, suitable for image generation AI models.

You MUST return valid JSON matching this exact structure:
{
    "prompts": [
        {
            "prompt": "Detailed technical prompt for image generation",
            "subject": "subject_name"
        },
        ... (one for each sticker subject)
    ],
    "background": {
        "prompt": "Background scene description",
        "subject": "background"
    }
}"""

    user_prompt = f"""Convert the following story beat into technical image generation prompts.

Story Beat:
Text: {beat.text}
Visual Description: {beat.visual_description}
Sticker Subjects: {', '.join(beat.sticker_subjects)}"""

    # Check if we need to use concise character reference (for GPT4All with 2048 token limit)
    # Always use concise when character reference is long, or if provider might fallback to GPT4All
    base_prompt_length = len(system_prompt) + len(user_prompt)
    use_concise = False
    
    if character_reference:
        # Use concise reference if:
        # 1. Currently using GPT4All
        # 2. Character reference is long (>1000 chars = ~250 tokens)
        # 3. Total prompt would be long (>5000 chars = ~1250 tokens, leaving room for GPT4All fallback)
        # 4. Provider is groq (might fallback to GPT4All on rate limit)
        if llm_client:
            if llm_client.provider == "gpt4all":
                use_concise = True
            elif llm_client.provider == "groq" and len(character_reference) > 1000:
                # Groq might rate limit and fallback to GPT4All, so use concise proactively
                use_concise = True
            elif base_prompt_length + len(character_reference) > 5000:
                use_concise = True
        elif len(character_reference) > 1000 or base_prompt_length + len(character_reference) > 5000:
            use_concise = True
        
        if use_concise and characters:
            # Use concise character reference
            from services.character_service import generate_concise_characters_reference
            concise_ref = generate_concise_characters_reference(characters)
            user_prompt += f"""

Character Reference (base design - characters must match this design but can vary in pose/action):
{concise_ref}"""
        else:
            user_prompt += f"""

Character Reference (base design - characters must match this design but can vary in pose/action):
{character_reference}"""

    if character_reference_image_path:
        user_prompt += f"""

Character Reference Image: {character_reference_image_path}
This is the base character design. Character images must match this design (colors, features, appearance) but can have different poses, actions, and expressions based on the story context."""

    if character_reference or character_reference_image_path:
        user_prompt += """

CRITICAL RULES FOR CHARACTER STICKERS:
- Each character sticker must show EXACTLY ONE SINGLE character ONLY
- NEVER mention other characters, interactions, or multiple characters in the prompt
- NEVER say "characters together", "interaction", "with [other character]", "meeting", or similar phrases
- For character subjects: Use the EXACT base design from the Character Reference (same colors, features, appearance)
- Add specific poses, actions, and emotions/expressions based on the story text and visual description
- Focus on clearly showing the character's emotional state (happy, sad, surprised, scared, etc.)
- Characters should vary in pose/action and emotion while maintaining visual consistency
- Start each character prompt with "SINGLE character only" or "ONE character only" to reinforce this"""

    user_prompt += "\n\nGenerate one technical image generation prompt for each sticker subject listed above.\nEach character sticker must show ONE character only - do not combine multiple characters.\nFocus on showing character emotions and expressions based on the story context.\n\nIMPORTANT: The background prompt should describe a COMPLETE full-page scene illustration that includes all story elements, characters, and environmental details. This will become a full-page image in the book.\n\nCRITICAL FOR BACKGROUND PROMPTS:\n- When describing characters in the background scene, you MUST explicitly state their SPECIES (human, animal type, etc.)\n- Include key character features and appearance details from the character reference\n- Example: Instead of saying 'a character', say 'a small brown mouse character with whiskers' or 'a tall human character with glasses'\n- NEVER change character species - if a character is described as a mouse, it must appear as a mouse in the scene, not as a human\n- Preserve all distinctive character features (colors, size, physical characteristics) from the character reference\n\nReturn only valid JSON, no additional text."

    try:
        content = await llm_client.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        prompt_data = json.loads(content)
        
        image_prompts = []
        # Get character names for validation
        character_names = [char.name.lower() for char in (characters or [])]
        
        for prompt_item in prompt_data.get("prompts", []):
            prompt_text = prompt_item.get("prompt", "")
            subject = prompt_item.get("subject", "")
            
            # Check if this is a character prompt
            is_character = any(char_name in subject.lower() or char_name in prompt_text.lower() 
                             for char_name in character_names)
            
            # Clean prompt to ensure single character only
            if is_character:
                prompt_text = clean_prompt_for_single_character(prompt_text)
            
            # Apply style keywords to prompt
            prompt_text = apply_style_to_prompt(prompt_text, style)
            
            image_prompt = ImagePrompt(
                prompt=prompt_text,
                subject=subject
            )
            image_prompts.append(image_prompt)
        
        if len(image_prompts) < len(beat.sticker_subjects):
            generated_subjects = {prompt.subject for prompt in image_prompts}
            for subject in beat.sticker_subjects:
                if subject not in generated_subjects:
                    simple_prompt = f"sticker-style {subject}, cute and colorful, clean white background, professional lighting, children's book illustration style"
                    # Apply style keywords to fallback prompt
                    simple_prompt = apply_style_to_prompt(simple_prompt, style)
                    image_prompts.append(ImagePrompt(
                        prompt=simple_prompt,
                        subject=subject
                    ))
        
        # Get background prompt
        background_prompt = None
        if "background" in prompt_data:
            bg_data = prompt_data["background"]
            bg_prompt_text = bg_data.get("prompt", f"Full-page children's book illustration scene: {beat.visual_description}, complete scene with all story elements")
        else:
            # Generate default background prompt (enhanced for full-page scenes)
            bg_prompt_text = f"Full-page children's book illustration scene: {beat.visual_description}, complete detailed scene with all characters and environmental elements, soft lighting, colorful and friendly, full page illustration"
        
        # Enhance background prompt with explicit character species and features
        if characters:
            bg_prompt_text = enhance_background_prompt_with_characters(bg_prompt_text, beat, characters)
        
        # Apply style keywords to background prompt
        bg_prompt_text = apply_style_to_prompt(bg_prompt_text, style)
        background_prompt = ImagePrompt(
            prompt=bg_prompt_text,
            subject="background"
        )
        
        return (image_prompts, background_prompt)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating image prompts: {e}")
