"""
Unit tests for PDF generator service.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from services.pdf_generator import (
    GridLayout,
    _calculate_grid_layout,
    StoryBookPDF,
    generate_pdf,
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    CANVAS_X,
    CANVAS_Y
)
from services.pdf_storage import get_pdf_path, pdf_exists, delete_pdf
from src.models import StoryBook, StoryBeat


class TestGridLayout:
    """Tests for GridLayout class."""
    
    def test_grid_layout_initialization(self):
        """Test GridLayout initialization."""
        layout = GridLayout(2, 2, 100.0, 150.0)
        assert layout.cols == 2
        assert layout.rows == 2
        assert layout.cell_width == 100.0
        assert layout.cell_height == 150.0
    
    def test_get_cell_position(self):
        """Test getting cell position in grid."""
        layout = GridLayout(2, 2, 100.0, 150.0)
        x, y = layout.get_cell_position(0, 0)
        assert x == CANVAS_X
        assert y == CANVAS_Y
        
        x, y = layout.get_cell_position(1, 1)
        expected_x = CANVAS_X + (1 * (100.0 + 10))  # cell_width + padding
        expected_y = CANVAS_Y + (1 * (150.0 + 10))
        assert x == expected_x
        assert y == expected_y


class TestCalculateGridLayout:
    """Tests for grid layout calculation."""
    
    def test_calculate_grid_layout_1_image(self):
        """Test grid layout for 1 image (centered)."""
        layout = _calculate_grid_layout(1)
        assert layout.cols == 1
        assert layout.rows == 1
        assert layout.cell_width > 0
        assert layout.cell_height > 0
        assert layout.cell_width == layout.cell_height  # Should be square
    
    def test_calculate_grid_layout_2_images(self):
        """Test grid layout for 2 images (side by side)."""
        layout = _calculate_grid_layout(2)
        assert layout.cols == 2
        assert layout.rows == 1
        assert layout.cell_width > 0
        assert layout.cell_height > 0
    
    def test_calculate_grid_layout_3_images(self):
        """Test grid layout for 3 images (2x2 grid)."""
        layout = _calculate_grid_layout(3)
        assert layout.cols == 2
        assert layout.rows == 2
        assert layout.cell_width > 0
        assert layout.cell_height > 0
    
    def test_calculate_grid_layout_many_images(self):
        """Test grid layout for many images (fallback to 2x2)."""
        layout = _calculate_grid_layout(10)
        assert layout.cols == 2
        assert layout.rows == 2


class TestStoryBookPDF:
    """Tests for StoryBookPDF class."""
    
    def test_pdf_initialization(self):
        """Test PDF initialization."""
        pdf = StoryBookPDF("Test Story")
        assert pdf.storybook_title == "Test Story"
    
    def test_footer_text_wrapping(self):
        """Test footer text wrapping functionality."""
        pdf = StoryBookPDF("Test Story")
        
        # Test with short text
        short_text = "This is a short paragraph."
        pdf.set_footer_text(short_text)
        pdf.add_page()
        # Should not raise exception
        
        # Test with long text
        long_text = " ".join(["Word"] * 100)  # Long text
        pdf.set_footer_text(long_text)
        pdf.add_page()
        # Should not raise exception and should wrap
    
    def test_place_sticker_with_mock_image(self, tmp_path):
        """Test placing a sticker with a mock image."""
        # Create a test image
        img_path = tmp_path / "test.png"
        img = Image.new('RGBA', (200, 200), (255, 0, 0, 255))
        img.save(img_path)
        
        pdf = StoryBookPDF("Test Story")
        pdf.add_page()
        
        # Place sticker without rotation
        pdf.place_sticker(
            str(img_path),
            x=100,
            y=100,
            width=150,
            height=150,
            rotation=0
        )
        # Should not raise exception
    
    def test_place_sticker_with_rotation(self, tmp_path):
        """Test placing a sticker with rotation."""
        # Create a test image
        img_path = tmp_path / "test.png"
        img = Image.new('RGBA', (200, 200), (0, 255, 0, 255))
        img.save(img_path)
        
        pdf = StoryBookPDF("Test Story")
        pdf.add_page()
        
        # Place sticker with rotation
        pdf.place_sticker(
            str(img_path),
            x=100,
            y=100,
            width=150,
            height=150,
            rotation=5.5
        )
        # Should not raise exception


class TestGeneratePDF:
    """Tests for PDF generation."""
    
    def test_generate_pdf_success(self, tmp_path):
        """Test successful PDF generation."""
        # Create test images
        job_id = "test_job"
        images_by_beat = {}
        
        for beat_num in range(1, 4):
            beat_images = []
            for i in range(2):  # 2 images per beat
                img_path = tmp_path / f"beat_{beat_num}_image_{i}.png"
                img = Image.new('RGBA', (200, 200), (100, 100, 200, 255))
                img.save(img_path)
                beat_images.append(str(img_path))
            images_by_beat[beat_num] = beat_images
        
        # Create storybook with 3 beats
        beats = []
        for i in range(3):
            beats.append(StoryBeat(
                text=f"Paragraph 1 of beat {i+1}.\n\nParagraph 2 of beat {i+1}.",
                visual_description=f"Visual {i+1}",
                sticker_subjects=[f"subject_{i+1}_1", f"subject_{i+1}_2"]
            ))
        
        storybook = StoryBook(
            title="Test Storybook",
            beats=beats
        )
        
        # Generate PDF
        pdf_path = generate_pdf(storybook, job_id, images_by_beat)
        
        # Verify PDF was created
        assert Path(pdf_path).exists()
        assert pdf_exists(job_id)
        
        # Verify PDF is not empty
        file_size = Path(pdf_path).stat().st_size
        assert file_size > 0
        
        # Cleanup
        delete_pdf(job_id)
    
    def test_generate_pdf_mismatched_beats(self, tmp_path):
        """Test PDF generation with mismatched beat/image counts."""
        job_id = "test_job"
        
        # Create storybook with 3 beats
        beats = [
            StoryBeat(
                text="Beat 1",
                visual_description="Visual 1",
                sticker_subjects=["subject1"]
            ),
            StoryBeat(
                text="Beat 2",
                visual_description="Visual 2",
                sticker_subjects=["subject2"]
            )
        ]
        
        storybook = StoryBook(
            title="Test Storybook",
            beats=beats
        )
        
        # Only provide images for 1 beat (mismatch)
        images_by_beat = {
            1: [str(tmp_path / "image1.png")]
        }
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Beat number mismatch"):
            generate_pdf(storybook, job_id, images_by_beat)
    
    def test_generate_pdf_missing_image_file(self):
        """Test PDF generation with missing image file."""
        job_id = "test_job"
        
        beats = [
            StoryBeat(
                text="Beat 1",
                visual_description="Visual 1",
                sticker_subjects=["subject1"]
            )
        ]
        
        storybook = StoryBook(
            title="Test Storybook",
            beats=beats
        )
        
        # Provide path to non-existent image
        images_by_beat = {
            1: ["/nonexistent/path/image.png"]
        }
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            generate_pdf(storybook, job_id, images_by_beat)


class TestPDFStorage:
    """Tests for PDF storage utilities."""
    
    def test_get_pdf_path(self):
        """Test getting PDF path."""
        job_id = "test_job_123"
        path = get_pdf_path(job_id)
        assert path.name == f"{job_id}.pdf"
        assert path.parent.name == "output"
    
    def test_pdf_exists_false(self):
        """Test pdf_exists returns False for non-existent PDF."""
        job_id = "nonexistent_job"
        assert pdf_exists(job_id) == False
    
    def test_delete_pdf_nonexistent(self):
        """Test deleting non-existent PDF doesn't raise error."""
        job_id = "nonexistent_job"
        # Should not raise exception
        delete_pdf(job_id)
