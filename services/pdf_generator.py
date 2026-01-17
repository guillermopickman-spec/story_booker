"""
PDF Generator: Creates storybook PDFs with text and sticker layouts.
"""

import os
import random
import math
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from io import BytesIO

from fpdf import FPDF  # fpdf2 package uses 'fpdf' as import name
from PIL import Image, ImageDraw
from dotenv import load_dotenv

from src.models import StoryBook, StoryBeat
from services.pdf_storage import save_pdf
from services.pod_preflight import (
    process_image_for_pod,
    get_pod_dimensions,
    get_safe_area,
    BLEED_SIZE,
    TRIM_MARGIN
)

load_dotenv()


# Page dimensions (US Letter: 8.5" x 11" = 612pt x 792pt)
PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN = 10
HEADER_HEIGHT = 50
FOOTER_HEIGHT = 150

CANVAS_WIDTH = PAGE_WIDTH - (2 * MARGIN)
CANVAS_HEIGHT = PAGE_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - (2 * MARGIN)
CANVAS_X = MARGIN
CANVAS_Y = HEADER_HEIGHT + MARGIN

CELL_PADDING = 10


class GridLayout:
    """Represents a grid layout configuration."""
    def __init__(self, cols: int, rows: int, cell_width: float, cell_height: float):
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height
    
    def get_cell_position(self, col: int, row: int) -> Tuple[float, float]:
        """Get the x, y position for a cell in the grid."""
        x = CANVAS_X + (col * (self.cell_width + CELL_PADDING))
        y = CANVAS_Y + (row * (self.cell_height + CELL_PADDING))
        return (x, y)


def _calculate_grid_layout(num_images: int) -> GridLayout:
    """
    Calculate optimal grid layout based on number of images.
    
    Args:
        num_images: Number of images to place (1-3)
        
    Returns:
        GridLayout object with grid configuration
    """
    if num_images == 1:
        cols, rows = 1, 1
        cell_width = min(CANVAS_WIDTH * 0.6, CANVAS_HEIGHT * 0.6)
        cell_height = cell_width
    
    elif num_images == 2:
        cols, rows = 2, 1
        available_width = CANVAS_WIDTH - CELL_PADDING
        cell_width = available_width / 2
        cell_height = min(cell_width, CANVAS_HEIGHT * 0.8)
    
    elif num_images == 3:
        cols, rows = 2, 2
        available_width = CANVAS_WIDTH - CELL_PADDING
        available_height = CANVAS_HEIGHT - CELL_PADDING
        cell_width = available_width / 2
        cell_height = available_height / 2
    
    else:
        cols, rows = 2, 2
        available_width = CANVAS_WIDTH - CELL_PADDING
        available_height = CANVAS_HEIGHT - CELL_PADDING
        cell_width = available_width / 2
        cell_height = available_height / 2
    
    return GridLayout(cols, rows, cell_width, cell_height)


class StoryBookPDF(FPDF):
    """Custom PDF class for storybook generation."""
    
    def __init__(self, title: str, pod_ready: bool = False):
        self.pod_ready = pod_ready
        
        # Adjust page dimensions for POD
        if pod_ready:
            page_width, page_height, _, _ = get_pod_dimensions()
            _, _, safe_width, _ = get_safe_area()
            # Initialize with custom page size (with bleeds)
            super().__init__(unit='pt', format=(page_width, page_height))
            self.footer_text_width = safe_width  # Use safe width for footer text
            self.page_height = page_height
        else:
            # Standard US Letter
            super().__init__(format='letter', unit='pt')
            self.footer_text_width = CANVAS_WIDTH  # Use canvas width for footer text
            self.page_height = PAGE_HEIGHT
        
        self.storybook_title = title
        self.page_footer_texts = {}
        self.page_backgrounds = {}
        
        self.set_auto_page_break(auto=False, margin=0)
        self.set_font("Helvetica", "B", 16)
    
    def header(self):
        """Draw header with title and page number."""
        self.set_font("Helvetica", "B", 16)
        self.set_xy(MARGIN, MARGIN)
        title_width = self.get_string_width(self.storybook_title)
        if title_width > PAGE_WIDTH - 2 * MARGIN - 50:
            title = self.storybook_title[:40] + "..."
        else:
            title = self.storybook_title
        self.cell(0, 20, title, 0, 1, "L")
        
        self.set_font("Helvetica", "", 10)
        page_num = f"Page {self.page_no()}"
        self.set_xy(PAGE_WIDTH - MARGIN - self.get_string_width(page_num), MARGIN + 5)
        self.cell(0, 10, page_num, 0, 0, "R")
    
    def footer(self):
        """Draw footer with story text (called automatically by FPDF)."""
        page_num = self.page_no()
        footer_text = self.page_footer_texts.get(page_num, "")
        
        if not footer_text:
            return
        
        # Use appropriate width and margins based on POD mode
        if self.pod_ready:
            safe_x, safe_y, safe_width, safe_height = get_safe_area()
            footer_x = safe_x
            footer_y = self.page_height - FOOTER_HEIGHT
            footer_text_width = safe_width
        else:
            footer_x = MARGIN
            footer_y = PAGE_HEIGHT - FOOTER_HEIGHT
            footer_text_width = self.footer_text_width
        
        self.set_font("Helvetica", "", 11)
        self.set_xy(footer_x, footer_y)
        
        paragraphs = footer_text.split("\n\n")
        
        y = footer_y
        line_height = 14
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            para = para.replace("\n", " ").strip()
            words = para.split()
            line = ""
            
            for word in words:
                test_line = line + (" " if line else "") + word
                width = self.get_string_width(test_line)
                
                if width > footer_text_width:
                    if line:
                        self.set_xy(footer_x, y)
                        self.cell(footer_text_width, line_height, line, 0, 1, "L")
                        y += line_height
                        line = word
                    else:
                        # Word is too long, truncate it
                        self.set_xy(footer_x, y)
                        truncated = word[:50] + "..." if len(word) > 50 else word
                        self.cell(footer_text_width, line_height, truncated, 0, 1, "L")
                        y += line_height
                        line = ""
                else:
                    line = test_line
            
            if line:
                self.set_xy(footer_x, y)
                self.cell(footer_text_width, line_height, line, 0, 1, "L")
                y += line_height
            
            y += line_height * 0.5
            
            if y > self.page_height - MARGIN:
                break
    
    def set_footer_text(self, text: str):
        """Set the footer text for the current page (call before add_page)."""
        next_page = self.page_no() + 1
        self.page_footer_texts[next_page] = text
    
    def set_background_image(self, image_path: str):
        """Set the background image for the current page (call before add_page)."""
        next_page = self.page_no() + 1
        self.page_backgrounds[next_page] = image_path
    
    def place_background(self):
        """Place background image on current page."""
        page_num = self.page_no()
        background_path = self.page_backgrounds.get(page_num)
        
        if background_path and Path(background_path).exists():
            try:
                with Image.open(background_path) as img:
                    # Resize background to fit canvas area
                    img = img.convert('RGB')
                    bg_width = int(CANVAS_WIDTH)
                    bg_height = int(CANVAS_HEIGHT)
                    img = img.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
                    
                    img_bytes = BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    # Place background in canvas area
                    self.image(img_bytes, x=CANVAS_X, y=CANVAS_Y, w=bg_width, h=bg_height)
            except Exception as e:
                # If background fails, continue without it
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to place background image: {e}")
    
    def place_sticker(
        self,
        image_path: str,
        x: float,
        y: float,
        width: float,
        height: float,
        rotation: float = 0
    ):
        """
        Place a sticker image with optional rotation.
        
        Args:
            image_path: Path to PNG image file
            x: X position in points
            y: Y position in points
            width: Width in points
            height: Height in points
            rotation: Rotation angle in degrees (-10 to 10)
        """
        with Image.open(image_path) as img:
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            cell_aspect = width / height
            
            if img_aspect > cell_aspect:
                new_width = int(width * 0.9)
                new_height = int(new_width / img_aspect)
            else:
                new_height = int(height * 0.9)
                new_width = int(new_height * img_aspect)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            if abs(rotation) > 0.1:
                img = img.rotate(rotation, expand=True, fillcolor=(255, 255, 255))
                new_width, new_height = img.size
                if new_width > width or new_height > height:
                    scale = min(width / new_width, height / new_height) * 0.9
                    new_width = int(new_width * scale)
                    new_height = int(new_height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            offset_x = (width - new_width) / 2
            offset_y = (height - new_height) / 2
            
            self.image(img_bytes, x=x + offset_x, y=y + offset_y, w=new_width, h=new_height)


def _interpolate_color(start_color: Tuple[int, int, int], end_color: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
    """
    Interpolate between two RGB colors.
    
    Args:
        start_color: Starting RGB color tuple
        end_color: Ending RGB color tuple
        ratio: Interpolation ratio (0.0 = start_color, 1.0 = end_color)
        
    Returns:
        Interpolated RGB color tuple
    """
    ratio = max(0.0, min(1.0, ratio))  # Clamp to [0, 1]
    r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
    g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
    b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
    return (r, g, b)


def _get_title_gradient_colors(title_length: int) -> List[Tuple[int, int, int]]:
    """
    Generate gradient colors for title letters.
    Creates a smooth color transition across the title.
    
    Args:
        title_length: Length of the title (number of characters)
        
    Returns:
        List of RGB color tuples, one for each character position
    """
    if title_length == 0:
        return []
    
    # Gradient from blue -> purple -> pink
    start_color = (100, 150, 255)  # Blue
    mid_color = (200, 100, 255)    # Purple
    end_color = (255, 150, 200)    # Pink
    
    colors = []
    for i in range(title_length):
        ratio = i / max(1, title_length - 1)  # 0.0 to 1.0
        
        if ratio < 0.5:
            # First half: blue to purple
            sub_ratio = ratio * 2
            color = _interpolate_color(start_color, mid_color, sub_ratio)
        else:
            # Second half: purple to pink
            sub_ratio = (ratio - 0.5) * 2
            color = _interpolate_color(mid_color, end_color, sub_ratio)
        
        colors.append(color)
    
    return colors


def _get_paragraph_colors(num_paragraphs: int) -> List[Tuple[int, int, int]]:
    """
    Generate color list for paragraphs.
    Uses a palette of bright, readable colors.
    
    Args:
        num_paragraphs: Number of paragraphs
        
    Returns:
        List of RGB color tuples, one for each paragraph
    """
    # Palette of bright, readable colors (with black stroke, these will be visible)
    color_palette = [
        (255, 255, 255),  # White
        (255, 255, 200),  # Light yellow
        (200, 255, 255),  # Light cyan
        (255, 200, 255),  # Light magenta
        (200, 255, 200),  # Light green
        (255, 240, 200),  # Light orange
        (240, 240, 255),  # Light blue
        (255, 220, 220),  # Light pink
    ]
    
    colors = []
    for i in range(num_paragraphs):
        colors.append(color_palette[i % len(color_palette)])
    
    return colors


def _draw_text_with_stroke(
    pdf: StoryBookPDF,
    text: str,
    x: float,
    y: float,
    font_size: float,
    text_color: Tuple[int, int, int],
    stroke_width: float = 2.0
):
    """
    Draw text with black stroke outline and colored fill.
    Uses manual multi-pass drawing for stroke effect.
    
    Args:
        pdf: StoryBookPDF instance
        text: Text to draw
        x: X position
        y: Y position
        font_size: Font size in points
        text_color: RGB color tuple for text fill
        stroke_width: Width of stroke outline (default: 2.0)
    """
    # Set font size
    pdf.set_font("Helvetica", "B", int(font_size))
    text_width = pdf.get_string_width(text)
    
    # Draw black stroke outline by drawing text multiple times around the position
    pdf.set_text_color(0, 0, 0)  # Black for stroke
    
    # Draw stroke in 8 directions (N, S, E, W, NE, NW, SE, SW)
    offsets = [
        (0, -stroke_width),      # N
        (0, stroke_width),       # S
        (-stroke_width, 0),       # W
        (stroke_width, 0),       # E
        (-stroke_width, -stroke_width),  # NW
        (stroke_width, -stroke_width),   # NE
        (-stroke_width, stroke_width),    # SW
        (stroke_width, stroke_width),    # SE
    ]
    
    for offset_x, offset_y in offsets:
        pdf.set_xy(x + offset_x, y + offset_y)
        pdf.cell(text_width, font_size + 4, text, 0, 0, "C")
    
    # Draw colored fill text on top
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.set_xy(x, y)
    pdf.cell(text_width, font_size + 4, text, 0, 0, "C")


def _draw_letter_with_stroke(
    pdf: StoryBookPDF,
    letter: str,
    x: float,
    y: float,
    font_size: float,
    text_color: Tuple[int, int, int],
    stroke_width: float = 2.0
) -> float:
    """
    Draw a single letter with black stroke outline and colored fill.
    Returns the width of the letter for positioning the next letter.
    
    Args:
        pdf: StoryBookPDF instance
        letter: Single character to draw
        x: X position
        y: Y position
        font_size: Font size in points
        text_color: RGB color tuple for text fill
        stroke_width: Width of stroke outline (default: 2.0)
        
    Returns:
        Width of the letter in points
    """
    # Set font size
    pdf.set_font("Helvetica", "B", int(font_size))
    letter_width = pdf.get_string_width(letter)
    
    # Draw black stroke outline
    pdf.set_text_color(0, 0, 0)  # Black for stroke
    
    # Draw stroke in 8 directions
    offsets = [
        (0, -stroke_width),
        (0, stroke_width),
        (-stroke_width, 0),
        (stroke_width, 0),
        (-stroke_width, -stroke_width),
        (stroke_width, -stroke_width),
        (-stroke_width, stroke_width),
        (stroke_width, stroke_width),
    ]
    
    for offset_x, offset_y in offsets:
        pdf.set_xy(x + offset_x, y + offset_y)
        pdf.cell(letter_width, font_size + 4, letter, 0, 0, "L")
    
    # Draw colored fill letter on top
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.set_xy(x, y)
    pdf.cell(letter_width, font_size + 4, letter, 0, 0, "L")
    
    return letter_width


def _create_cover_page(
    pdf: StoryBookPDF,
    title: str,
    cover_image_path: Optional[str],
    pod_ready: bool = False
):
    """
    Create a full-bleed cover page with title overlay.
    
    Args:
        pdf: StoryBookPDF instance
        title: Storybook title
        cover_image_path: Optional path to cover image
        pod_ready: If True, use POD dimensions and safe margins
    """
    pdf.add_page()
    
    # Store original title for truncation check
    original_title = title
    
    # Get page dimensions
    if pod_ready:
        page_width, page_height, trim_width, trim_height = get_pod_dimensions()
        safe_x, safe_y, safe_width, safe_height = get_safe_area()
    else:
        page_width = PAGE_WIDTH
        page_height = PAGE_HEIGHT
        trim_width = PAGE_WIDTH
        trim_height = PAGE_HEIGHT
        safe_x = MARGIN
        safe_y = MARGIN
        safe_width = PAGE_WIDTH - (2 * MARGIN)
        safe_height = PAGE_HEIGHT - (2 * MARGIN)
    
    # Place cover image if available (full-bleed)
    if cover_image_path and Path(cover_image_path).exists():
        try:
            with Image.open(cover_image_path) as cover_img:
                # Convert to RGB if CMYK (for display, but CMYK will be preserved in PDF)
                if cover_img.mode == 'CMYK':
                    # For CMYK, we'll keep it but FPDF2 might convert to RGB
                    # This is a limitation we'll accept for now
                    cover_img = cover_img.convert('RGB')
                else:
                    cover_img = cover_img.convert('RGB')
                # Resize to full page dimensions (including bleeds if POD)
                cover_img = cover_img.resize((int(page_width), int(page_height)), Image.Resampling.LANCZOS)
                
                img_bytes = BytesIO()
                cover_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Place image at full page (0, 0) with full dimensions (including bleeds)
                pdf.image(img_bytes, x=0, y=0, w=page_width, h=page_height)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to place cover image: {e}. Creating text-only cover.")
            # Fill with light background color if image fails
            pdf.set_fill_color(240, 240, 240)
            pdf.rect(0, 0, page_width, page_height, 'F')
    else:
        # No cover image - create text-only cover with background
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(0, 0, page_width, page_height, 'F')
    
    # Calculate dynamic font size for title
    # Start at 48pt and scale down if needed
    font_size = 48
    max_title_width = safe_width * 0.8  # 80% of safe width
    
    pdf.set_font("Helvetica", "B", int(font_size))
    title_width = pdf.get_string_width(title)
    
    # Scale down font if title is too wide
    while title_width > max_title_width and font_size > 20:
        font_size -= 2
        pdf.set_font("Helvetica", "B", int(font_size))
        title_width = pdf.get_string_width(title)
    
    # If still too wide, truncate title (but keep font size readable)
    if title_width > max_title_width and font_size <= 20:
        # Truncate title to fit
        while title_width > max_title_width and len(title) > 1:
            title = title[:-1]
            pdf.set_font("Helvetica", "B", int(font_size))
            title_width = pdf.get_string_width(title)
        if len(title) < len(original_title):
            title = title + "..."
    
    # Get gradient colors for title
    gradient_colors = _get_title_gradient_colors(len(title))
    
    # Calculate total width of title to center it
    pdf.set_font("Helvetica", "B", int(font_size))
    total_title_width = pdf.get_string_width(title)
    
    # Position title in safe area, centered horizontally
    if pod_ready:
        title_x = safe_x + (safe_width - total_title_width) / 2
        title_y = safe_y + (safe_height * 0.2)  # Upper portion of safe area
    else:
        title_x = (page_width - total_title_width) / 2
        title_y = page_height * 0.25  # Upper third
    
    # Draw each letter with its gradient color and stroke outline
    current_x = title_x
    for i, letter in enumerate(title):
        if letter == ' ':
            # For spaces, just advance position
            pdf.set_font("Helvetica", "B", int(font_size))
            space_width = pdf.get_string_width(' ')
            current_x += space_width
        else:
            # Draw letter with gradient color and stroke
            letter_color = gradient_colors[i] if i < len(gradient_colors) else gradient_colors[-1]
            letter_width = _draw_letter_with_stroke(
                pdf, letter, current_x, title_y, int(font_size), letter_color, stroke_width=2.5
            )
            current_x += letter_width


def _create_gradient_background(page_width: float = PAGE_WIDTH, page_height: float = PAGE_HEIGHT) -> Image.Image:
    """
    Create a vertical gradient background image for back cover.
    
    Args:
        page_width: Page width in points
        page_height: Page height in points
    
    Returns:
        PIL Image object with RGB gradient background
    """
    # Create image with page dimensions
    img = Image.new('RGB', (int(page_width), int(page_height)))
    draw = ImageDraw.Draw(img)
    
    # Gradient colors: Vibrant sky blue -> Bright pink -> Rich lavender
    # Made more vibrant and noticeable
    start_color = (180, 220, 255)  # Vibrant sky blue
    mid_color = (255, 180, 220)    # Bright pink
    end_color = (220, 200, 255)    # Rich lavender
    
    # Draw vertical gradient line by line
    for y in range(int(page_height)):
        ratio = y / page_height  # 0.0 at top, 1.0 at bottom
        
        if ratio < 0.5:
            # First half: sky blue to pink
            sub_ratio = ratio * 2
            color = _interpolate_color(start_color, mid_color, sub_ratio)
        else:
            # Second half: pink to lavender
            sub_ratio = (ratio - 0.5) * 2
            color = _interpolate_color(mid_color, end_color, sub_ratio)
        
        # Draw horizontal line
        draw.line([(0, y), (page_width, y)], fill=color)
    
    return img


def _create_texture_overlay(page_width: float = PAGE_WIDTH, page_height: float = PAGE_HEIGHT) -> Image.Image:
    """
    Create a subtle texture overlay for background.
    
    Args:
        page_width: Page width in points
        page_height: Page height in points
    
    Returns:
        PIL Image object with RGBA texture pattern
    """
    # Create RGBA image for texture
    img = Image.new('RGBA', (int(page_width), int(page_height)), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Create visible paper texture with random dots and patterns
    # Increased opacity and density for more noticeable texture
    opacity = int(255 * 0.25)  # 25% opacity (increased from 12%)
    
    # Add more texture dots for paper texture
    num_dots = int(page_width * page_height / 100)  # Increased density (was /200)
    for _ in range(num_dots):
        x = random.randint(0, int(page_width) - 1)
        y = random.randint(0, int(page_height) - 1)
        # Random gray color with opacity
        gray_value = random.randint(150, 200)
        dot_color = (gray_value, gray_value, gray_value, opacity)
        # Draw slightly larger dots
        radius = random.randint(1, 3)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=dot_color)
    
    # Add some subtle lines for additional texture
    for _ in range(int(page_width * page_height / 500)):
        x1 = random.randint(0, int(page_width) - 1)
        y1 = random.randint(0, int(page_height) - 1)
        x2 = x1 + random.randint(-20, 20)
        y2 = y1 + random.randint(-20, 20)
        line_opacity = int(255 * 0.15)
        line_color = (180, 180, 180, line_opacity)
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=1)
    
    return img


def _apply_background_to_pdf(
    pdf: StoryBookPDF,
    gradient: Image.Image,
    texture: Optional[Image.Image] = None,
    pod_ready: bool = False,
    page_width: float = PAGE_WIDTH,
    page_height: float = PAGE_HEIGHT
):
    """
    Apply gradient background and optional texture to PDF page.
    
    Args:
        pdf: StoryBookPDF instance
        gradient: Gradient background image
        texture: Optional texture overlay image
        pod_ready: If True, use POD dimensions
        page_width: Page width in points
        page_height: Page height in points
    """
    # Composite texture over gradient if provided
    if texture:
        # Convert gradient to RGBA for compositing
        background = gradient.convert('RGBA')
        # Composite texture over gradient (texture has alpha channel)
        background = Image.alpha_composite(background, texture)
        # Convert back to RGB for PDF
        background = background.convert('RGB')
    else:
        background = gradient
    
    # Convert to bytes and place in PDF
    img_bytes = BytesIO()
    background.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Place background at full page (including bleeds if POD)
    pdf.image(img_bytes, x=0, y=0, w=page_width, h=page_height)


def _create_back_cover_page(
    pdf: StoryBookPDF,
    synopsis: str,
    language: Optional[str] = None,
    pod_ready: bool = False
):
    """
    Create a beautiful back cover page with gradient background, styled heading, and enhanced synopsis.
    
    Args:
        pdf: StoryBookPDF instance
        synopsis: Story synopsis text
        language: Language code ("es" for Spanish, "en" for English, default: "en")
        pod_ready: If True, use POD dimensions and safe margins
    """
    pdf.add_page()
    
    # Get page dimensions
    if pod_ready:
        page_width, page_height, trim_width, trim_height = get_pod_dimensions()
        safe_x, safe_y, safe_width, safe_height = get_safe_area()
    else:
        page_width = PAGE_WIDTH
        page_height = PAGE_HEIGHT
        trim_width = PAGE_WIDTH
        trim_height = PAGE_HEIGHT
        safe_x = MARGIN
        safe_y = MARGIN
        safe_width = PAGE_WIDTH - (2 * MARGIN)
        safe_height = PAGE_HEIGHT - (2 * MARGIN)
    
    # Create and apply gradient background with texture
    gradient = _create_gradient_background(page_width, page_height)
    texture = _create_texture_overlay(page_width, page_height)
    
    _apply_background_to_pdf(pdf, gradient, texture, pod_ready=pod_ready, page_width=page_width, page_height=page_height)
    
    # Add styled heading: Language-aware
    heading_text = "Sobre Esta Historia" if language == "es" else "About This Story"
    heading_font_size = 30
    pdf.set_font("Helvetica", "B", int(heading_font_size))
    
    # Get gradient colors for heading
    heading_gradient_colors = _get_title_gradient_colors(len(heading_text))
    
    # Calculate heading position (centered, top section - in safe area if POD)
    total_heading_width = pdf.get_string_width(heading_text)
    if pod_ready:
        heading_x = safe_x + (safe_width - total_heading_width) / 2
        heading_y = safe_y + 20
    else:
        heading_x = (page_width - total_heading_width) / 2
        heading_y = 80
    
    # Draw each letter of heading with gradient color and stroke
    current_x = heading_x
    for i, letter in enumerate(heading_text):
        if letter == ' ':
            pdf.set_font("Helvetica", "B", int(heading_font_size))
            space_width = pdf.get_string_width(' ')
            current_x += space_width
        else:
            letter_color = heading_gradient_colors[i] if i < len(heading_gradient_colors) else heading_gradient_colors[-1]
            letter_width = _draw_letter_with_stroke(
                pdf, letter, current_x, heading_y, int(heading_font_size), letter_color, stroke_width=2.5
            )
            current_x += letter_width
    
    # Synopsis section with enhanced styling
    if pod_ready:
        synopsis_margin = TRIM_MARGIN
        synopsis_width = safe_width
        synopsis_y_start = heading_y + 50  # Below heading
        synopsis_max_height = safe_height * 0.4
    else:
        synopsis_margin = 60
        synopsis_width = page_width - (2 * synopsis_margin)
        synopsis_y_start = heading_y + 70  # Below heading
        synopsis_max_height = page_height * 0.45
    
    # Word wrap synopsis
    pdf.set_font("Helvetica", "B", 16)  # Larger, bold font
    words = synopsis.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = pdf.get_string_width(test_line)
        
        if test_width > synopsis_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    
    # Get gradient colors for synopsis lines
    synopsis_gradient_colors = _get_title_gradient_colors(len(lines)) if lines else []
    
    # Draw synopsis lines with gradient colors and stroke outline
    line_height = 22
    font_size = 16
    y = synopsis_y_start
    for line_idx, line in enumerate(lines):
        if y > synopsis_y_start + synopsis_max_height:
            break
        
        # Get gradient color for this line
        line_color = synopsis_gradient_colors[line_idx] if line_idx < len(synopsis_gradient_colors) else synopsis_gradient_colors[-1] if synopsis_gradient_colors else (255, 255, 255)
        
        # Center the line
        line_width = pdf.get_string_width(line)
        if pod_ready:
            line_x = safe_x + (safe_width - line_width) / 2
        else:
            line_x = (page_width - line_width) / 2
        
        # Draw text with stroke outline
        _draw_text_with_stroke(
            pdf, line, line_x, y, font_size, line_color, stroke_width=2.0
        )
        
        y += line_height
    
    # Bottom section: "Produced by Story Booker" branding
    # Use darker color for better visibility on gradient background
    if pod_ready:
        branding_y = safe_y + safe_height - 30
    else:
        branding_y = page_height - 80
    pdf.set_font("Helvetica", "B", 11)  # Slightly larger and bold
    pdf.set_text_color(100, 100, 100)  # Darker gray for visibility
    branding_text = "Produced by Story Booker"
    branding_width = pdf.get_string_width(branding_text)
    if pod_ready:
        pdf.set_xy(safe_x + (safe_width - branding_width) / 2, branding_y)
    else:
        pdf.set_xy((page_width - branding_width) / 2, branding_y)
    pdf.cell(branding_width, 11, branding_text, 0, 0, "C")
    
    # Bottom-right: ISBN barcode placeholder
    # Standard barcode size: approximately 2" x 1" = 144pt x 72pt
    barcode_width = 144
    barcode_height = 72
    if pod_ready:
        barcode_x = safe_x + safe_width - barcode_width - 20
        barcode_y = safe_y + safe_height - barcode_height - 20
    else:
        barcode_x = page_width - barcode_width - 40
        barcode_y = page_height - barcode_height - 40
    
    # Draw barcode placeholder rectangle with white background for visibility
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(barcode_x, barcode_y, barcode_width, barcode_height, 'F')
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(1)
    pdf.rect(barcode_x, barcode_y, barcode_width, barcode_height, 'D')
    
    # Add placeholder text
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    placeholder_text = "ISBN Barcode"
    placeholder_width = pdf.get_string_width(placeholder_text)
    pdf.set_xy(barcode_x + (barcode_width - placeholder_width) / 2, barcode_y + barcode_height / 2)
    pdf.cell(placeholder_width, 8, placeholder_text, 0, 0, "C")
    
    # Reset text color to black for other pages
    pdf.set_text_color(0, 0, 0)


def _create_about_author_page(
    pdf: StoryBookPDF,
    author_bio: str,
    language: Optional[str] = None
):
    """
    Create an "About the Author" page with author biography.
    
    Args:
        pdf: StoryBookPDF instance
        author_bio: Author biography text
        language: Language code ("es" for Spanish, "en" for English, default: "en")
    """
    pdf.add_page()
    
    # Background color (subtle, matching book style)
    pdf.set_fill_color(250, 250, 250)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, 'F')
    
    # Page title: Language-aware (centered, larger font, bold)
    title_y = 150
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 0, 0)
    title_text = "Sobre el Autor" if language == "es" else "About the Author"
    title_width = pdf.get_string_width(title_text)
    pdf.set_xy((PAGE_WIDTH - title_width) / 2, title_y)
    pdf.cell(title_width, 24, title_text, 0, 0, "C")
    
    # Author bio section (centered with margins)
    bio_margin = 80
    bio_width = PAGE_WIDTH - (2 * bio_margin)
    bio_y_start = title_y + 80
    bio_max_height = PAGE_HEIGHT - bio_y_start - 100
    
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(0, 0, 0)
    
    # Word wrap author bio
    words = author_bio.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = pdf.get_string_width(test_line)
        
        if test_width > bio_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    
    # Draw bio lines (centered)
    line_height = 20
    y = bio_y_start
    for line in lines:
        if y > bio_y_start + bio_max_height:
            break
        line_width = pdf.get_string_width(line)
        pdf.set_xy((PAGE_WIDTH - line_width) / 2, y)
        pdf.cell(line_width, line_height, line, 0, 1, "C")
        y += line_height


def _create_story_page(
    pdf: StoryBookPDF,
    beat: StoryBeat,
    fullpage_image_path: Optional[str],
    pod_ready: bool = False
):
    """
    Create a full-page story page with image and overlaid text.
    
    Args:
        pdf: StoryBookPDF instance
        beat: StoryBeat with text content
        fullpage_image_path: Optional path to full-page scene image
        pod_ready: If True, use POD dimensions and safe margins
    """
    pdf.add_page()
    
    # Get page dimensions
    if pod_ready:
        page_width, page_height, trim_width, trim_height = get_pod_dimensions()
        safe_x, safe_y, safe_width, safe_height = get_safe_area()
    else:
        page_width = PAGE_WIDTH
        page_height = PAGE_HEIGHT
        trim_width = PAGE_WIDTH
        trim_height = PAGE_HEIGHT
        safe_x = MARGIN
        safe_y = MARGIN
        safe_width = PAGE_WIDTH - (2 * MARGIN)
        safe_height = PAGE_HEIGHT - (2 * MARGIN)
    
    # Place full-page image if available (full-bleed)
    if fullpage_image_path and Path(fullpage_image_path).exists():
        try:
            with Image.open(fullpage_image_path) as story_img:
                # Convert to RGB if CMYK (for display, but CMYK will be preserved in PDF)
                if story_img.mode == 'CMYK':
                    # For CMYK, we'll keep it but FPDF2 might convert to RGB
                    story_img = story_img.convert('RGB')
                else:
                    story_img = story_img.convert('RGB')
                # Resize to full page dimensions (including bleeds if POD)
                story_img = story_img.resize((int(page_width), int(page_height)), Image.Resampling.LANCZOS)
                
                img_bytes = BytesIO()
                story_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Place image at full page (0, 0) with full dimensions (including bleeds)
                pdf.image(img_bytes, x=0, y=0, w=page_width, h=page_height)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to place story page image: {e}. Creating text-only page.")
            # Fill with light background color if image fails
            pdf.set_fill_color(240, 240, 240)
            pdf.rect(0, 0, page_width, page_height, 'F')
    else:
        # No image - create text-only page with background
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(0, 0, page_width, page_height, 'F')
    
    # Overlay story text in lower portion of page (within safe area if POD)
    story_text = beat.text
    if not story_text:
        return
    
    # Text positioning: bottom portion of page with margins
    if pod_ready:
        text_margin = TRIM_MARGIN  # Use trim margin for POD
        text_width = safe_width
        text_x_start = safe_x  # Start position for text area
        text_y_start = safe_y + (safe_height * 0.6)  # Lower portion of safe area
        text_max_height = safe_height * 0.35  # Use up to 35% of safe height for text
    else:
        text_margin = 60
        text_width = page_width - (2 * text_margin)
        text_x_start = text_margin  # Start position for text area
        text_y_start = page_height * 0.7  # Start at 70% from top (bottom 30%)
        text_max_height = page_height * 0.25  # Use up to 25% of page height for text
    
    # Font sizing: start at 14pt, scale down if needed
    font_size = 14
    line_height = 18
    
    pdf.set_font("Helvetica", "", int(font_size))
    
    # Word wrap story text and track which paragraph each line belongs to
    paragraphs = story_text.split("\n\n")
    lines_with_para = []  # List of (line_text, paragraph_index)
    
    # Get colors for paragraphs
    para_colors = _get_paragraph_colors(len([p for p in paragraphs if p.strip()]))
    para_index = 0
    
    for para in paragraphs:
        if not para.strip():
            continue
        
        para = para.replace("\n", " ").strip()
        words = para.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = pdf.get_string_width(test_line)
            
            if test_width > text_width:
                if current_line:
                    lines_with_para.append((current_line, para_index))
                current_line = word
            else:
                current_line = test_line
        
        if current_line:
            lines_with_para.append((current_line, para_index))
        
        para_index += 1
    
    # Draw text lines with stroke outline and paragraph colors
    y = text_y_start
    for line_text, para_idx in lines_with_para:
        if y > text_y_start + text_max_height:
            break
        
        if line_text:  # Skip empty lines
            line_width = pdf.get_string_width(line_text)
            # Center text within the text area (respecting margins), not the full page
            line_x = text_x_start + (text_width - line_width) / 2
            
            # Get color for this paragraph
            para_color = para_colors[para_idx] if para_idx < len(para_colors) else para_colors[0]
            
            # Draw text with stroke outline
            _draw_text_with_stroke(
                pdf, line_text, line_x, y, font_size, para_color, stroke_width=2.0
            )
        
        y += line_height
    
    # Reset text color to black for other pages
    pdf.set_text_color(0, 0, 0)


def _create_page_layout(
    pdf: StoryBookPDF,
    beat: StoryBeat,
    images: List[str],
    background_path: Optional[str],
    page_num: int
):
    """
    Create a single page with header, footer, background, and sticker layout.
    
    Args:
        pdf: StoryBookPDF instance
        beat: StoryBeat with text content
        images: List of image file paths for this beat
        background_path: Optional path to background image
        page_num: Page number (for display)
    """
    pdf.set_footer_text(beat.text)
    if background_path:
        pdf.set_background_image(background_path)
    pdf.add_page()
    
    # Place background first (if exists)
    pdf.place_background()
    
    if images:
        num_images = len(images)
        grid = _calculate_grid_layout(num_images)
        
        rotation_min = float(os.getenv("STICKER_ROTATION_MIN", "-10"))
        rotation_max = float(os.getenv("STICKER_ROTATION_MAX", "10"))
        
        image_idx = 0
        for row in range(grid.rows):
            for col in range(grid.cols):
                if image_idx >= num_images:
                    break
                
                x, y = grid.get_cell_position(col, row)
                rotation = random.uniform(rotation_min, rotation_max)
                
                pdf.place_sticker(
                    images[image_idx],
                    x, y,
                    grid.cell_width,
                    grid.cell_height,
                    rotation
                )
                
                image_idx += 1
            
            if image_idx >= num_images:
                break


def generate_pdf(
    storybook: StoryBook,
    job_id: str,
    image_paths: Dict[int, Optional[str]],
    cover_image_path: Optional[str] = None,
    synopsis: Optional[str] = None,
    language: Optional[str] = None,
    pod_ready: bool = False
) -> str:
    """
    Generate a PDF storybook from a storybook and image paths.
    
    Args:
        storybook: StoryBook object with title and beats
        job_id: Unique job identifier
        image_paths: Dictionary mapping beat number (1-indexed) to full-page image path (or None)
        cover_image_path: Optional path to cover image for front cover page
        synopsis: Optional synopsis text for back cover page
        language: Optional language code (e.g., "en", "es")
        pod_ready: If True, generate POD-ready PDF with CMYK and bleeds
        
    Returns:
        Absolute path to generated PDF file
        
    Raises:
        ValueError: If number of beats doesn't match number of image groups
        FileNotFoundError: If any image file doesn't exist
    """
    expected_beat_nums = set(range(1, len(storybook.beats) + 1))
    found_beat_nums = set(image_paths.keys())
    
    if expected_beat_nums != found_beat_nums:
        missing = expected_beat_nums - found_beat_nums
        extra = found_beat_nums - expected_beat_nums
        error_msg = (
            f"Beat number mismatch! Expected beats {sorted(expected_beat_nums)}, "
            f"found {sorted(found_beat_nums)}. "
        )
        if missing:
            error_msg += f"Missing: {sorted(missing)}. "
        if extra:
            error_msg += f"Extra: {sorted(extra)}."
        raise ValueError(error_msg)
    
    # Validate image paths
    for beat_num, image_path in image_paths.items():
        if image_path and not Path(image_path).exists():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Full-page image not found for beat {beat_num}: {image_path}. Continuing without image.")
    
    # Process images for POD if needed
    processed_images = {}
    processed_cover = None
    
    if pod_ready:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Processing images for POD (CMYK conversion and bleed addition)...")
        
        # Process cover image
        if cover_image_path and Path(cover_image_path).exists():
            try:
                _, processed_cover = process_image_for_pod(cover_image_path)
                logger.info(f"Processed cover image for POD: {processed_cover}")
            except Exception as e:
                logger.warning(f"Failed to process cover image for POD: {e}. Using original.")
                processed_cover = cover_image_path
        
        # Process story page images
        for beat_num, image_path in image_paths.items():
            if image_path and Path(image_path).exists():
                try:
                    _, processed_path = process_image_for_pod(image_path)
                    processed_images[beat_num] = processed_path
                    logger.info(f"Processed image for beat {beat_num}: {processed_path}")
                except Exception as e:
                    logger.warning(f"Failed to process image for beat {beat_num}: {e}. Using original.")
                    processed_images[beat_num] = image_path
            else:
                processed_images[beat_num] = image_path
    else:
        processed_images = image_paths
        processed_cover = cover_image_path
    
    # Log POD readiness status
    import logging
    logger = logging.getLogger(__name__)
    if pod_ready:
        page_width, page_height, trim_width, trim_height = get_pod_dimensions()
        safe_x, safe_y, safe_width, safe_height = get_safe_area()
        logger.info("="*60)
        logger.info("POD-READY PDF GENERATION ENABLED")
        logger.info("="*60)
        logger.info(f"Page dimensions (with bleed): {page_width:.1f} x {page_height:.1f} pt")
        logger.info(f"Trim size: {trim_width:.1f} x {trim_height:.1f} pt")
        logger.info(f"Safe area: x={safe_x:.1f}, y={safe_y:.1f}, w={safe_width:.1f}, h={safe_height:.1f} pt")
        logger.info(f"Bleed size: {BLEED_SIZE:.1f} pt, Trim margin: {TRIM_MARGIN:.1f} pt")
        logger.info("Images will be converted to CMYK and extended with bleed")
        logger.info("="*60)
    
    pdf = StoryBookPDF(storybook.title, pod_ready=pod_ready)
    
    # Create front cover page (Page 0) if cover image is available
    if processed_cover:
        _create_cover_page(pdf, storybook.title, processed_cover, pod_ready=pod_ready)
    
    # Create story pages with full-page images
    for i, beat in enumerate(storybook.beats, 1):
        fullpage_image_path = processed_images.get(i)
        _create_story_page(pdf, beat, fullpage_image_path, pod_ready=pod_ready)
    
    # Create "About the Author" page if author_bio is available
    if storybook.author_bio:
        _create_about_author_page(pdf, storybook.author_bio, language)
    
    # Create back cover page if synopsis is available
    if synopsis:
        _create_back_cover_page(pdf, synopsis, language, pod_ready=pod_ready)
    
    pdf_bytes = pdf.output(dest='S')
    
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    elif isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    
    pdf_path = save_pdf(job_id, pdf_bytes, language)
    
    return pdf_path
