"""
Sticker Generator: Complete pipeline for generating stickers from image prompts.
Combines image generation, background removal, and storage.
"""

import os
from typing import List, Optional
from src.models import ImagePrompt
from services.image_service import ImageService, get_image_service
from services.background_remover import process_image
from services.image_storage import ensure_job_directory, get_image_path
from dotenv import load_dotenv

load_dotenv()


async def generate_sticker(
    prompt: ImagePrompt,
    job_id: str,
    beat_num: int,
    image_service: Optional[ImageService] = None,
    bg_threshold: Optional[int] = None,
    autocrop_padding: Optional[int] = None,
    index: Optional[int] = None
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
        size="1024x1024"
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


async def generate_stickers_for_beat(
    prompts: List[ImagePrompt],
    job_id: str,
    beat_num: int,
    image_service: Optional[ImageService] = None,
    bg_threshold: Optional[int] = None,
    autocrop_padding: Optional[int] = None
) -> List[str]:
    """
    Generate all stickers for a story beat.
    
    Args:
        prompts: List of ImagePrompt objects for the beat
        job_id: Unique job identifier
        beat_num: Story beat number (1-indexed)
        image_service: Optional pre-configured image service
        bg_threshold: Background removal threshold
        autocrop_padding: Padding for autocrop
        
    Returns:
        List of paths to saved sticker images
    """
    image_paths = []
    
    subject_counts = {}
    for prompt in prompts:
        subject = prompt.subject
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    subject_indices = {}
    
    for prompt in prompts:
        subject = prompt.subject
        
        if subject_counts[subject] > 1:
            if subject not in subject_indices:
                subject_indices[subject] = 0
            subject_indices[subject] += 1
            index = subject_indices[subject]
        else:
            index = None
        
        path = await generate_sticker(
            prompt=prompt,
            job_id=job_id,
            beat_num=beat_num,
            image_service=image_service,
            bg_threshold=bg_threshold,
            autocrop_padding=autocrop_padding,
            index=index
        )
        image_paths.append(path)
    
    return image_paths
