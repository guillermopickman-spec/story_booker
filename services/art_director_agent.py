"""
Art Director Agent: Converts story beats into technical image generation prompts.
"""

import json
from typing import List, Optional
from services.llm_client import get_llm_client, LLMClient
from src.models import StoryBeat, ImagePrompt


async def generate_image_prompts(
    beat: StoryBeat,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    llm_client: Optional[LLMClient] = None
) -> List[ImagePrompt]:
    """
    Convert a story beat into technical 3D-modeling prompts for image generation.
    Generates one prompt per sticker subject.
    
    Args:
        beat: The StoryBeat to convert into image prompts
        provider: LLM provider to use (groq, openai, gpt4all). Defaults to groq.
        model: Model name to use (provider-specific)
        llm_client: Optional pre-configured LLM client
        
    Returns:
        List of ImagePrompt objects, one per sticker subject
    """
    if llm_client is None:
        llm_client = get_llm_client(provider=provider, model=model)
    system_prompt = """You are an expert art director specializing in 3D modeling and rendering. 
Your task is to create technical, detailed prompts for generating "sticker-style" images.

Each image should be:
- Sticker-style with clean, bold outlines
- 3D rendered or illustrated
- Suitable for transparent background (PNG)
- Bright, colorful, and child-friendly
- Detailed enough for a professional 3D modeler to understand

For each sticker subject, create a prompt that describes:
- The main subject in detail (character, object, etc.)
- The style (cute, playful, realistic 3D, etc.)
- Lighting and composition
- Color palette
- Technical details (shadows, highlights, etc.)

The prompts should be technical but clear, suitable for image generation AI models.

You MUST return valid JSON matching this exact structure:
{
    "prompts": [
        {
            "prompt": "Detailed technical prompt for image generation",
            "subject": "subject_name"
        },
        ... (one for each sticker subject)
    ]
}"""

    user_prompt = f"""Convert the following story beat into technical image generation prompts.

Story Beat:
Text: {beat.text}
Visual Description: {beat.visual_description}
Sticker Subjects: {', '.join(beat.sticker_subjects)}

Generate one technical image generation prompt for each sticker subject listed above.
Return only valid JSON, no additional text."""

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
        for prompt_item in prompt_data.get("prompts", []):
            image_prompt = ImagePrompt(**prompt_item)
            image_prompts.append(image_prompt)
        
        if len(image_prompts) < len(beat.sticker_subjects):
            generated_subjects = {prompt.subject for prompt in image_prompts}
            for subject in beat.sticker_subjects:
                if subject not in generated_subjects:
                    simple_prompt = f"3D rendered sticker-style {subject}, cute and colorful, clean white background, professional lighting, children's book illustration style"
                    image_prompts.append(ImagePrompt(
                        prompt=simple_prompt,
                        subject=subject
                    ))
        
        return image_prompts
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating image prompts: {e}")
