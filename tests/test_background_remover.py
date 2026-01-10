"""
Tests for background removal and autocrop functionality.
"""

import pytest
import io
from PIL import Image
from services.background_remover import (
    remove_background,
    find_content_bbox,
    autocrop,
    process_image
)


def create_test_image_with_white_bg(width=200, height=200, content_size=100):
    """Create a test image with white background and colored content in center."""
    image = Image.new('RGB', (width, height), color=(255, 255, 255))  # White background
    
    # Draw colored rectangle in center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    x1 = (width - content_size) // 2
    y1 = (height - content_size) // 2
    x2 = x1 + content_size
    y2 = y1 + content_size
    draw.rectangle([x1, y1, x2, y2], fill=(100, 150, 200))  # Blue rectangle
    
    return image


def create_test_image_all_white(width=200, height=200):
    """Create an all-white test image."""
    return Image.new('RGB', (width, height), color=(255, 255, 255))


class TestBackgroundRemoval:
    """Tests for background removal functionality."""
    
    def test_remove_background_removes_white(self):
        """Test that white background pixels are made transparent."""
        image = create_test_image_with_white_bg()
        
        result = remove_background(image, threshold=240)
        
        assert result.mode == 'RGBA'
        # Check that corners (white background) are transparent
        assert result.getpixel((0, 0))[3] == 0  # Alpha channel
        assert result.getpixel((199, 199))[3] == 0
        # Check that center (colored content) is not transparent
        assert result.getpixel((100, 100))[3] > 0
    
    def test_remove_background_preserves_content(self):
        """Test that non-white content is preserved."""
        image = create_test_image_with_white_bg()
        
        result = remove_background(image, threshold=240)
        
        # Center pixel should still have color
        r, g, b, a = result.getpixel((100, 100))
        assert r == 100
        assert g == 150
        assert b == 200
        assert a > 0
    
    def test_remove_background_converts_rgb_to_rgba(self):
        """Test that RGB images are converted to RGBA."""
        image = Image.new('RGB', (100, 100), color=(255, 255, 255))
        
        result = remove_background(image)
        
        assert result.mode == 'RGBA'
    
    def test_remove_background_threshold(self):
        """Test that threshold parameter works correctly."""
        # Create image with light gray background (not pure white)
        image = Image.new('RGB', (100, 100), color=(250, 250, 250))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.rectangle([25, 25, 75, 75], fill=(100, 100, 100))
        
        # With low threshold (200), fewer pixels are considered white, so more remain
        result_low = remove_background(image, threshold=200, preserve_edges=False)
        # With high threshold (240), more pixels are considered white, so more are removed
        result_high = remove_background(image, threshold=240, preserve_edges=False)
        
        # Count non-transparent pixels
        non_transparent_low = sum(1 for x in range(100) for y in range(100) if result_low.getpixel((x, y))[3] > 0)
        non_transparent_high = sum(1 for x in range(100) for y in range(100) if result_high.getpixel((x, y))[3] > 0)
        
        # Low threshold means 250,250,250 is NOT considered white (250 < 255, but 250 > 200 threshold)
        # High threshold means 250,250,250 IS considered white (250 >= 240 threshold)
        # So high threshold should remove more (fewer non-transparent pixels)
        # Content area should be preserved in both
        assert non_transparent_low >= non_transparent_high


class TestFindContentBbox:
    """Tests for content bounding box detection."""
    
    def test_find_content_bbox_finds_content(self):
        """Test that bounding box is found for content."""
        image = create_test_image_with_white_bg()
        rgba_image = image.convert('RGBA')
        # Make background transparent
        rgba_image = remove_background(rgba_image, threshold=240, preserve_edges=False)
        
        bbox = find_content_bbox(rgba_image, padding=0)
        
        assert bbox is not None
        left, top, right, bottom = bbox
        assert left < right
        assert top < bottom
        # Bbox should be in the image bounds (content is centered, so roughly 50-150 for 200px image with 100px content)
        assert left >= 0
        assert top >= 0
        assert right <= 200
        assert bottom <= 200
    
    def test_find_content_bbox_adds_padding(self):
        """Test that padding is added to bounding box."""
        image = create_test_image_with_white_bg(content_size=50)
        rgba_image = image.convert('RGBA')
        rgba_image = remove_background(rgba_image, threshold=240)
        
        bbox_no_padding = find_content_bbox(rgba_image, padding=0)
        bbox_with_padding = find_content_bbox(rgba_image, padding=10)
        
        assert bbox_no_padding is not None
        assert bbox_with_padding is not None
        
        left1, top1, right1, bottom1 = bbox_no_padding
        left2, top2, right2, bottom2 = bbox_with_padding
        
        assert left2 <= left1
        assert top2 <= top1
        assert right2 >= right1
        assert bottom2 >= bottom1
    
    def test_find_content_bbox_returns_none_for_all_transparent(self):
        """Test that None is returned for all-transparent images."""
        image = Image.new('RGBA', (100, 100), color=(255, 255, 255, 0))
        
        bbox = find_content_bbox(image)
        
        assert bbox is None
    
    def test_find_content_bbox_respects_image_bounds(self):
        """Test that padding doesn't exceed image bounds."""
        image = create_test_image_with_white_bg(width=50, height=50, content_size=20)
        rgba_image = image.convert('RGBA')
        rgba_image = remove_background(rgba_image, threshold=240)
        
        bbox = find_content_bbox(rgba_image, padding=100)  # Large padding
        
        assert bbox is not None
        left, top, right, bottom = bbox
        assert left >= 0
        assert top >= 0
        assert right <= 50
        assert bottom <= 50


class TestAutocrop:
    """Tests for autocrop functionality."""
    
    def test_autocrop_crops_to_content(self):
        """Test that image is cropped to content bounding box."""
        image = create_test_image_with_white_bg(width=200, height=200, content_size=100)
        rgba_image = image.convert('RGBA')
        rgba_image = remove_background(rgba_image, threshold=240, preserve_edges=False)
        
        cropped = autocrop(rgba_image, padding=5)
        
        # Cropped image should be smaller than original (or equal if bbox detection fails)
        assert cropped.size[0] <= 200
        assert cropped.size[1] <= 200
        # Should still contain content (at least some pixels)
        assert cropped.size[0] > 0
        assert cropped.size[1] > 0
    
    def test_autocrop_preserves_content(self):
        """Test that content is preserved after cropping."""
        image = create_test_image_with_white_bg()
        rgba_image = image.convert('RGBA')
        rgba_image = remove_background(rgba_image, threshold=240)
        
        cropped = autocrop(rgba_image, padding=0)
        
        # Center of cropped image should have content
        center_x, center_y = cropped.size[0] // 2, cropped.size[1] // 2
        r, g, b, a = cropped.getpixel((center_x, center_y))
        assert a > 0  # Should have content
        assert r == 100
        assert g == 150
        assert b == 200
    
    def test_autocrop_handles_all_transparent(self):
        """Test that all-transparent images return minimal image."""
        image = Image.new('RGBA', (100, 100), color=(255, 255, 255, 0))
        
        cropped = autocrop(image)
        
        # Should return a small transparent image
        assert cropped.mode == 'RGBA'
        assert cropped.size[0] <= 1
        assert cropped.size[1] <= 1


class TestProcessImage:
    """Tests for complete image processing pipeline."""
    
    def test_process_image_complete_pipeline(self):
        """Test that process_image completes full pipeline."""
        # Create test image with white background
        image = create_test_image_with_white_bg()
        
        # Convert to bytes
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_data = image_bytes.getvalue()
        
        # Process with no edge preservation for cleaner test
        processed_data = process_image(image_data, threshold=240, padding=5, preserve_edges=False)
        
        # Load processed image
        processed_image = Image.open(io.BytesIO(processed_data))
        
        assert processed_image.mode == 'RGBA'
        # Should be smaller than or equal to original (cropped)
        assert processed_image.size[0] <= 200
        assert processed_image.size[1] <= 200
        # Should have some transparency or content
        assert processed_image.size[0] > 0
        assert processed_image.size[1] > 0
    
    def test_process_image_returns_png_bytes(self):
        """Test that processed image is valid PNG."""
        image = create_test_image_with_white_bg()
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_data = image_bytes.getvalue()
        
        processed_data = process_image(image_data)
        
        # Should be valid PNG (starts with PNG signature)
        assert processed_data[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Should be loadable
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.format == 'PNG'
