"""
Tests for sticker generator integration.
"""

import pytest
import os
import io
from pathlib import Path
from unittest.mock import AsyncMock, patch
from PIL import Image
from src.models import ImagePrompt
from services.sticker_generator import generate_sticker, generate_stickers_for_beat
from services.image_service import ImageService


class TestStickerGenerator:
    """Tests for sticker generation pipeline."""
    
    @pytest.fixture(autouse=True)
    def cleanup_test_files(self):
        """Clean up test files after each test."""
        yield
        # Clean up test assets for multiple test job IDs
        import shutil
        for job_id in ["test_job", "test_filename_fix"]:
            test_dir = Path("assets") / job_id
            if test_dir.exists():
                shutil.rmtree(test_dir)
    
    @pytest.mark.asyncio
    async def test_generate_sticker_complete_pipeline(self):
        """Test complete sticker generation pipeline."""
        prompt = ImagePrompt(
            prompt="3D rendered sticker-style mouse, cute and colorful",
            subject="mouse"
        )
        
        # Mock image service
        mock_service = AsyncMock(spec=ImageService)
        # Create mock PNG bytes
        test_image = Image.new('RGB', (100, 100), color=(255, 255, 255))
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='PNG')
        mock_service.generate_image = AsyncMock(return_value=image_bytes.getvalue())
        
        path = await generate_sticker(
            prompt=prompt,
            job_id="test_job",
            beat_num=1,
            image_service=mock_service
        )
        
        assert os.path.exists(path)
        assert path.endswith(".png")
        assert "beat_1" in path
        assert "mouse" in path.lower()
        
        # Verify image was processed (should be smaller due to cropping white)
        with open(path, 'rb') as f:
            processed_image = Image.open(io.BytesIO(f.read()))
            assert processed_image.mode == 'RGBA'
    
    @pytest.mark.asyncio
    async def test_generate_stickers_for_beat(self):
        """Test generating multiple stickers for a beat."""
        prompts = [
            ImagePrompt(prompt="test prompt 1", subject="mouse"),
            ImagePrompt(prompt="test prompt 2", subject="tree")
        ]
        
        # Mock image service
        mock_service = AsyncMock(spec=ImageService)
        test_image = Image.new('RGB', (100, 100), color=(255, 255, 255))
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='PNG')
        mock_service.generate_image = AsyncMock(return_value=image_bytes.getvalue())
        
        paths = await generate_stickers_for_beat(
            prompts=prompts,
            job_id="test_job",
            beat_num=2,
            image_service=mock_service
        )
        
        assert len(paths) == 2
        assert all(os.path.exists(p) for p in paths)
        assert all("beat_2" in p for p in paths)
        
        # Verify different subjects in paths
        assert any("mouse" in p.lower() for p in paths)
        assert any("tree" in p.lower() for p in paths)
    
    @pytest.mark.asyncio
    async def test_filename_collision_fix(self):
        """Test that duplicate subjects get unique filenames with numbered suffixes."""
        from services.image_storage import list_job_images, cleanup_job_assets
        
        prompts = [
            ImagePrompt(subject="cats", prompt="A cat"),
            ImagePrompt(subject="cats", prompt="Another cat"),
            ImagePrompt(subject="mouse", prompt="A mouse"),
        ]
        
        job_id = "test_filename_fix"
        beat_num = 1
        
        # Mock image service
        mock_service = AsyncMock(spec=ImageService)
        test_image = Image.new('RGB', (100, 100), color=(255, 255, 255))
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='PNG')
        mock_service.generate_image = AsyncMock(return_value=image_bytes.getvalue())
        
        try:
            paths = await generate_stickers_for_beat(
                prompts=prompts,
                job_id=job_id,
                beat_num=beat_num,
                image_service=mock_service
            )
            
            # Verify we got 3 paths
            assert len(paths) == 3
            
            # Get all generated files
            all_files = list_job_images(job_id)
            actual_files = {Path(f).name for f in all_files}
            
            # Expected filenames (duplicate subjects should be numbered)
            expected_files = {
                "beat_1_cats_1.png",
                "beat_1_cats_2.png",
                "beat_1_mouse.png",
            }
            
            # Verify all expected files exist
            for expected in expected_files:
                assert expected in actual_files, f"Expected file {expected} not found. Found: {actual_files}"
            
            # Verify file count matches
            assert len(actual_files) == len(expected_files)
            
            # Verify alpha channel preservation (all should be RGBA)
            for file_path in all_files:
                with Image.open(file_path) as img:
                    assert img.mode == 'RGBA', f"File {Path(file_path).name} should be RGBA mode, got {img.mode}"
        finally:
            # Cleanup test files
            cleanup_job_assets(job_id)
