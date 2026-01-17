"""
POD Preflight Service: Converts PDFs to Print-on-Demand (KDP) ready format.

Handles CMYK color conversion, bleed addition, and margin compliance for Amazon KDP.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

from PIL import Image, ImageCms

try:
    from reportlab.lib.units import inch  # type: ignore
except ImportError as e:
    raise

logger = logging.getLogger(__name__)

# KDP Requirements
BLEED_SIZE = 0.125 * inch  # 0.125 inches = 9 points at 72 DPI
TRIM_MARGIN = 0.25 * inch  # Minimum margin from trim edge
SAFE_MARGIN = TRIM_MARGIN + BLEED_SIZE  # Margin from bleed edge

# Page dimensions with bleeds
PAGE_WIDTH_WITH_BLEED = 8.5 * inch + (2 * BLEED_SIZE)  # 8.5" + 0.25" = 8.75"
PAGE_HEIGHT_WITH_BLEED = 11 * inch + (2 * BLEED_SIZE)  # 11" + 0.25" = 11.25"

# Trim size (actual page size)
TRIM_WIDTH = 8.5 * inch
TRIM_HEIGHT = 11 * inch

# Safe area (where text should be)
SAFE_WIDTH = TRIM_WIDTH - (2 * TRIM_MARGIN)
SAFE_HEIGHT = TRIM_HEIGHT - (2 * TRIM_MARGIN)


def convert_image_to_cmyk(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert RGB image to CMYK color space.
    
    Args:
        image_path: Path to RGB image file
        output_path: Optional output path. If None, saves next to original with _cmyk suffix
        
    Returns:
        Path to converted CMYK image file
    """
    if output_path is None:
        path_obj = Path(image_path)
        output_path = str(path_obj.parent / f"{path_obj.stem}_cmyk{path_obj.suffix}")
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Initialize CMYK image variable
            img_cmyk: Optional[Image.Image] = None
            
            # Try to use ICC profile for accurate CMYK conversion
            try:
                # Use sRGB profile as source
                srgb_profile = ImageCms.createProfile('sRGB')
                
                # Try to get a standard CMYK profile from system
                # ImageCms.createProfile() only supports 'LAB', 'XYZ', 'sRGB'
                # For CMYK, we need to load an ICC file or use simple conversion
                cmyk_profile = None
                
                # Try common system CMYK profile locations
                cmyk_profile_paths = [
                    # Windows common locations
                    r'C:\Windows\System32\spool\drivers\color\USWebCoatedSWOP.icc',
                    r'C:\Windows\System32\spool\drivers\color\ISOcoated_v2_300_eci.icc',
                    # macOS common locations
                    '/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc',
                    '/Library/ColorSync/Profiles/Generic CMYK Profile.icc',
                    # Linux common locations
                    '/usr/share/color/icc/colord/USWebCoatedSWOP.icc',
                ]
                
                for profile_path in cmyk_profile_paths:
                    if os.path.exists(profile_path):
                        try:
                            cmyk_profile = ImageCms.getOpenProfile(profile_path)
                            logger.info(f"Using CMYK profile: {profile_path}")
                            break
                        except Exception:
                            continue
                
                if cmyk_profile is not None:
                    # Convert using color management
                    img_cmyk = ImageCms.profileToProfile(
                        img, srgb_profile, cmyk_profile, outputMode='CMYK'
                    )
                else:
                    # No CMYK profile found, use simple conversion
                    raise Exception("No system CMYK profile found")
                    
            except Exception as e:
                logger.warning(f"ICC profile conversion failed: {e}. Using simple RGB->CMYK conversion.")
                # Fallback: simple RGB to CMYK conversion
                img_cmyk = img.convert('CMYK')
            
            # Ensure img_cmyk is defined (should always be at this point)
            if img_cmyk is None:
                img_cmyk = img.convert('CMYK')
            
            # Save CMYK image
            img_cmyk.save(output_path, format='PNG', optimize=True)
            logger.info(f"Converted {image_path} to CMYK: {output_path}")
            return output_path
            
    except Exception as e:
        logger.error(f"Failed to convert image to CMYK: {e}")
        raise


def extend_image_with_bleed(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Extend image by adding bleed area (0.125" on all sides).
    Uses edge pixel replication for seamless extension.
    
    Args:
        image_path: Path to image file
        output_path: Optional output path. If None, saves next to original with _bleed suffix
        
    Returns:
        Path to extended image file
    """
    if output_path is None:
        path_obj = Path(image_path)
        output_path = str(path_obj.parent / f"{path_obj.stem}_bleed{path_obj.suffix}")
    
    try:
        with Image.open(image_path) as img:
            # Calculate bleed pixels (0.125" at 72 DPI = 9 pixels, but we need higher res)
            # Assume image is at reasonable resolution, calculate bleed in pixels
            width, height = img.size
            
            # Calculate bleed in pixels (0.125" = 9pt, but we need to scale based on image DPI)
            # For a typical 1024x1024 image on 8.5x11 page, that's about 1024/8.5 = 120 DPI
            # So 0.125" = 0.125 * 120 = 15 pixels approximately
            # More accurately: if image is sized for PAGE_WIDTH, bleed = (BLEED_SIZE / PAGE_WIDTH) * width
            bleed_pixels_x = int((BLEED_SIZE / TRIM_WIDTH) * width)
            bleed_pixels_y = int((BLEED_SIZE / TRIM_HEIGHT) * height)
            
            # Create new image with bleed
            new_width = width + (2 * bleed_pixels_x)
            new_height = height + (2 * bleed_pixels_y)
            
            # Create extended image
            if img.mode == 'RGBA':
                extended = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 0))
            else:
                extended = Image.new(img.mode, (new_width, new_height), (255, 255, 255))
            
            # Paste original image in center
            extended.paste(img, (bleed_pixels_x, bleed_pixels_y))
            
            # Extend edges by copying edge pixels
            # Top edge
            top_edge = img.crop((0, 0, width, 1))
            for y in range(bleed_pixels_y):
                extended.paste(top_edge.resize((width, 1)), (bleed_pixels_x, y))
            
            # Bottom edge
            bottom_edge = img.crop((0, height - 1, width, height))
            for y in range(new_height - bleed_pixels_y, new_height):
                extended.paste(bottom_edge.resize((width, 1)), (bleed_pixels_x, y))
            
            # Left edge
            left_edge = img.crop((0, 0, 1, height))
            for x in range(bleed_pixels_x):
                extended.paste(left_edge.resize((1, height)), (x, bleed_pixels_y))
            
            # Right edge
            right_edge = img.crop((width - 1, 0, width, height))
            for x in range(new_width - bleed_pixels_x, new_width):
                extended.paste(right_edge.resize((1, height)), (x, bleed_pixels_y))
            
            # Corners (use corner pixels)
            # Helper to get default pixel value based on mode
            def get_default_pixel(mode: str):
                """Get default white pixel value for given image mode."""
                if mode == 'RGBA':
                    return (255, 255, 255, 0)
                elif mode == 'CMYK':
                    return (0, 0, 0, 0)  # White in CMYK
                elif mode == 'RGB':
                    return (255, 255, 255)
                elif mode == 'L':  # Grayscale
                    return 255
                else:
                    # Fallback: use white RGB as default
                    return (255, 255, 255)
            
            # Top-left
            top_left = img.getpixel((0, 0))
            if top_left is None:
                top_left = get_default_pixel(img.mode)
            for y in range(bleed_pixels_y):
                for x in range(bleed_pixels_x):
                    extended.putpixel((x, y), top_left)
            
            # Top-right
            top_right = img.getpixel((width - 1, 0))
            if top_right is None:
                top_right = get_default_pixel(img.mode)
            for y in range(bleed_pixels_y):
                for x in range(new_width - bleed_pixels_x, new_width):
                    extended.putpixel((x, y), top_right)
            
            # Bottom-left
            bottom_left = img.getpixel((0, height - 1))
            if bottom_left is None:
                bottom_left = get_default_pixel(img.mode)
            for y in range(new_height - bleed_pixels_y, new_height):
                for x in range(bleed_pixels_x):
                    extended.putpixel((x, y), bottom_left)
            
            # Bottom-right
            bottom_right = img.getpixel((width - 1, height - 1))
            if bottom_right is None:
                bottom_right = get_default_pixel(img.mode)
            for y in range(new_height - bleed_pixels_y, new_height):
                for x in range(new_width - bleed_pixels_x, new_width):
                    extended.putpixel((x, y), bottom_right)
            
            # Save extended image
            extended.save(output_path, format='PNG', optimize=True)
            logger.info(f"Extended {image_path} with bleed: {output_path}")
            return output_path
            
    except Exception as e:
        logger.error(f"Failed to extend image with bleed: {e}")
        raise


def process_image_for_pod(image_path: str, temp_dir: Optional[Path] = None) -> Tuple[str, str]:
    """
    Process image for POD: convert to CMYK and add bleed.
    
    Args:
        image_path: Path to original RGB image
        temp_dir: Optional temporary directory for processed images
        
    Returns:
        Tuple of (cmyk_image_path, cmyk_bleed_image_path)
    """
    if temp_dir is None:
        temp_dir = Path(image_path).parent
    else:
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to CMYK
    cmyk_path = str(temp_dir / f"{Path(image_path).stem}_cmyk.png")
    cmyk_image_path = convert_image_to_cmyk(image_path, cmyk_path)
    
    # Add bleed
    bleed_path = str(temp_dir / f"{Path(image_path).stem}_cmyk_bleed.png")
    cmyk_bleed_image_path = extend_image_with_bleed(cmyk_image_path, bleed_path)
    
    return cmyk_image_path, cmyk_bleed_image_path


def get_pod_dimensions() -> Tuple[float, float, float, float]:
    """
    Get POD page dimensions.
    
    Returns:
        Tuple of (page_width, page_height, trim_width, trim_height) in points
    """
    return (
        PAGE_WIDTH_WITH_BLEED,
        PAGE_HEIGHT_WITH_BLEED,
        TRIM_WIDTH,
        TRIM_HEIGHT
    )


def get_safe_area() -> Tuple[float, float, float, float]:
    """
    Get safe area dimensions (where text should be placed).
    
    Returns:
        Tuple of (safe_x, safe_y, safe_width, safe_height) in points
    """
    safe_x = BLEED_SIZE + TRIM_MARGIN
    safe_y = BLEED_SIZE + TRIM_MARGIN
    return (safe_x, safe_y, SAFE_WIDTH, SAFE_HEIGHT)
