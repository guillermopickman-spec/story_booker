"""
Background Remover: Removes white/light backgrounds and crops images to content.
"""

import os
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter
import io


def remove_background(
    image: Image.Image,
    threshold: int = 240,
    preserve_edges: bool = True
) -> Image.Image:
    """
    Remove white/light background by setting alpha channel to 0.
    
    Args:
        image: PIL Image object (RGB or RGBA)
        threshold: RGB threshold for white detection (0-255, default 240)
        preserve_edges: If True, preserve anti-aliased edges
        
    Returns:
        RGBA Image with transparent background
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    result = Image.new('RGBA', image.size, (0, 0, 0, 0))
    pixels = image.load()
    result_pixels = result.load()
    width, height = image.size
    
    white_threshold = threshold
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            is_white = r >= white_threshold and g >= white_threshold and b >= white_threshold
            
            if is_white:
                white_distance = math.sqrt(
                    (r - 255) ** 2 + (g - 255) ** 2 + (b - 255) ** 2
                )
                
                if preserve_edges and white_distance > 10:
                    edge_range = 30
                    if white_distance < edge_range:
                        alpha_factor = white_distance / edge_range
                        new_alpha = int(255 * (1.0 - alpha_factor) * 0.3)
                        result_pixels[x, y] = (r, g, b, new_alpha)
                    else:
                        result_pixels[x, y] = (r, g, b, 0)
                else:
                    result_pixels[x, y] = (r, g, b, 0)
            else:
                result_pixels[x, y] = (r, g, b, a)
    
    return result


def find_content_bbox(image: Image.Image, padding: int = 10) -> Optional[Tuple[int, int, int, int]]:
    """
    Find bounding box of non-transparent content.
    
    Args:
        image: PIL Image object (RGBA)
        padding: Padding to add around content (in pixels)
        
    Returns:
        Tuple of (left, top, right, bottom) or None if no content found
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    alpha = image.split()[3]
    bbox = alpha.getbbox()
    
    if bbox is None:
        return None
    
    left, top, right, bottom = bbox
    width, height = image.size
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(width, right + padding)
    bottom = min(height, bottom + padding)
    
    return (left, top, right, bottom)


def autocrop(image: Image.Image, padding: int = 10) -> Image.Image:
    """
    Crop image to content bounding box with padding.
    
    Args:
        image: PIL Image object (RGBA)
        padding: Padding to add around content (in pixels)
        
    Returns:
        Cropped Image
    """
    bbox = find_content_bbox(image, padding)
    
    if bbox is None:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    
    left, top, right, bottom = bbox
    return image.crop((left, top, right, bottom))


def add_sticker_border(image: Image.Image, border_width: int = 3) -> Image.Image:
    """
    Add a white stroke border around non-transparent pixels.
    
    Uses a dilation approach: creates a mask of non-transparent pixels,
    dilates it, then subtracts the original to get just the border area.
    
    Args:
        image: PIL Image object (RGBA)
        border_width: Width of the border in pixels
        
    Returns:
        Image with white border added
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    
    # Create a new image with extra space for the border
    border_padding = border_width + 2
    new_width = width + (border_padding * 2)
    new_height = height + (border_padding * 2)
    
    result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    result.paste(image, (border_padding, border_padding), image)
    
    alpha = result.split()[3]
    mask = alpha.point(lambda x: 255 if x > 0 else 0, mode='L')
    
    dilated_mask = Image.new('L', (new_width, new_height), 0)
    mask_pixels = mask.load()
    dilated_pixels = dilated_mask.load()
    
    for y in range(new_height):
        for x in range(new_width):
            if mask_pixels[x, y] > 0:
                dilated_pixels[x, y] = 255
            else:
                for dy in range(-border_width, border_width + 1):
                    for dx in range(-border_width, border_width + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < new_width and 0 <= ny < new_height:
                            if mask_pixels[nx, ny] > 0:
                                distance = math.sqrt(dx*dx + dy*dy)
                                if distance <= border_width:
                                    dilated_pixels[x, y] = 255
                                    break
                    if dilated_pixels[x, y] > 0:
                        break
    
    border_mask = Image.new('L', (new_width, new_height), 0)
    border_pixels = border_mask.load()
    for y in range(new_height):
        for x in range(new_width):
            if dilated_pixels[x, y] > 0 and mask_pixels[x, y] == 0:
                border_pixels[x, y] = 255
    
    result_pixels = result.load()
    for y in range(new_height):
        for x in range(new_width):
            if border_pixels[x, y] > 0:
                result_pixels[x, y] = (255, 255, 255, 255)
    
    return result


def process_image(
    image_data: bytes,
    threshold: int = 240,
    padding: int = 10,
    preserve_edges: bool = True,
    add_border: bool = False
) -> bytes:
    """
    Complete image processing pipeline: background removal + autocrop + optional border.
    
    Args:
        image_data: Raw image bytes
        threshold: RGB threshold for white detection
        padding: Padding for autocrop
        preserve_edges: Preserve anti-aliased edges
        add_border: If True, add white border around sticker
        
    Returns:
        Processed image as PNG bytes
    """
    image = Image.open(io.BytesIO(image_data))
    
    image = remove_background(image, threshold=threshold, preserve_edges=preserve_edges)
    image = autocrop(image, padding=padding)
    
    if add_border:
        border_width = int(os.getenv("STICKER_BORDER_WIDTH", "3"))
        image = add_sticker_border(image, border_width=border_width)
    
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def process_image_file(
    input_path: str,
    output_path: str,
    threshold: int = 240,
    padding: int = 10,
    preserve_edges: bool = True
):
    """
    Process an image file: load, remove background, crop, and save.
    
    Args:
        input_path: Path to input image file
        output_path: Path to save processed image
        threshold: RGB threshold for white detection
        padding: Padding for autocrop
        preserve_edges: Preserve anti-aliased edges
    """
    with open(input_path, 'rb') as f:
        image_data = f.read()
    
    processed_data = process_image(
        image_data,
        threshold=threshold,
        padding=padding,
        preserve_edges=preserve_edges
    )
    
    with open(output_path, 'wb') as f:
        f.write(processed_data)
