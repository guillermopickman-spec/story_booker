"""
Image Storage: Manages file system operations for storing processed sticker images.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict


def ensure_job_directory(job_id: str) -> Path:
    """
    Ensure the assets directory for a job exists.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Path object for the job's assets directory
    """
    assets_dir = Path("assets") / job_id
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def get_image_path(job_id: str, beat_num: int, subject: str, index: Optional[int] = None) -> Path:
    """
    Get the file path for a sticker image.
    
    Args:
        job_id: Unique job identifier
        beat_num: Story beat number (1-indexed)
        subject: Subject name for the sticker
        index: Optional index to add when there are duplicate subjects (1-indexed)
        
    Returns:
        Path object for the image file
    """
    assets_dir = ensure_job_directory(job_id)
    safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_subject = safe_subject.replace(' ', '_')
    
    if index is not None:
        filename = f"beat_{beat_num}_{safe_subject}_{index}.png"
    else:
        filename = f"beat_{beat_num}_{safe_subject}.png"
    
    return assets_dir / filename


def save_image(image_path: Path, image_data: bytes) -> str:
    """
    Save image data to file.
    
    Args:
        image_path: Path where image should be saved
        image_data: Raw image bytes
        
    Returns:
        String path to saved file
    """
    with open(image_path, 'wb') as f:
        f.write(image_data)
    return str(image_path)


def list_job_images(job_id: str) -> List[str]:
    """
    List all image files for a job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        List of image file paths (relative to project root)
    """
    assets_dir = Path("assets") / job_id
    if not assets_dir.exists():
        return []
    
    images = [str(p) for p in assets_dir.glob("*.png")]
    return sorted(images)


def get_job_images_by_beat(job_id: str) -> Dict[int, List[str]]:
    """
    Get all images for a job organized by beat number.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Dictionary mapping beat number (1-indexed) to list of image paths
    """
    assets_dir = Path("assets") / job_id
    if not assets_dir.exists():
        return {}
    
    images_by_beat: Dict[int, List[str]] = {}
    
    pattern = re.compile(r'beat_(\d+)_')
    
    for image_path in assets_dir.glob("*.png"):
        match = pattern.search(image_path.name)
        if match:
            beat_num = int(match.group(1))
            if beat_num not in images_by_beat:
                images_by_beat[beat_num] = []
            images_by_beat[beat_num].append(str(image_path))
    
    for beat_num in images_by_beat:
        images_by_beat[beat_num].sort()
    
    return images_by_beat


def cleanup_job_assets(job_id: str):
    """
    Remove all assets for a job (cleanup function).
    
    Args:
        job_id: Unique job identifier
    """
    assets_dir = Path("assets") / job_id
    if assets_dir.exists():
        import shutil
        shutil.rmtree(assets_dir)
