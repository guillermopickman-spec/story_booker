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
from PIL import Image
from dotenv import load_dotenv

from src.models import StoryBook, StoryBeat
from services.pdf_storage import save_pdf

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
    
    def __init__(self, title: str):
        super().__init__(format='letter', unit='pt')
        self.storybook_title = title
        self.page_footer_texts = {}
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
        
        self.set_font("Helvetica", "", 11)
        self.set_xy(MARGIN, PAGE_HEIGHT - FOOTER_HEIGHT)
        
        paragraphs = footer_text.split("\n\n")
        
        y = PAGE_HEIGHT - FOOTER_HEIGHT
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
                
                if width > CANVAS_WIDTH:
                    if line:
                        self.set_xy(MARGIN, y)
                        self.cell(CANVAS_WIDTH, line_height, line, 0, 1, "L")
                        y += line_height
                        line = word
                    else:
                        self.set_xy(MARGIN, y)
                        self.cell(CANVAS_WIDTH, line_height, word[:50] + "...", 0, 1, "L")
                        y += line_height
                        line = ""
                else:
                    line = test_line
            
            if line:
                self.set_xy(MARGIN, y)
                self.cell(CANVAS_WIDTH, line_height, line, 0, 1, "L")
                y += line_height
            
            y += line_height * 0.5
            
            if y > PAGE_HEIGHT - MARGIN:
                break
    
    def set_footer_text(self, text: str):
        """Set the footer text for the current page (call before add_page)."""
        next_page = self.page_no() + 1
        self.page_footer_texts[next_page] = text
    
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


def _create_page_layout(
    pdf: StoryBookPDF,
    beat: StoryBeat,
    images: List[str],
    page_num: int
):
    """
    Create a single page with header, footer, and sticker layout.
    
    Args:
        pdf: StoryBookPDF instance
        beat: StoryBeat with text content
        images: List of image file paths for this beat
        page_num: Page number (for display)
    """
    pdf.set_footer_text(beat.text)
    pdf.add_page()
    
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
    image_paths: Dict[int, List[str]]
) -> str:
    """
    Generate a PDF storybook from a storybook and image paths.
    
    Args:
        storybook: StoryBook object with title and beats
        job_id: Unique job identifier
        image_paths: Dictionary mapping beat number (1-indexed) to list of image paths
        
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
    
    for beat_num, paths in image_paths.items():
        for path in paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Image file not found: {path}")
    
    pdf = StoryBookPDF(storybook.title)
    
    for i, beat in enumerate(storybook.beats, 1):
        beat_images = image_paths.get(i, [])
        _create_page_layout(pdf, beat, beat_images, i)
    
    pdf_bytes = pdf.output(dest='S')
    
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    elif isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    
    pdf_path = save_pdf(job_id, pdf_bytes)
    
    return pdf_path
