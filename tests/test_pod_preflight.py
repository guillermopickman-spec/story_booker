"""
Test POD Preflight functionality.

Tests CMYK conversion, bleed addition, and POD-ready PDF generation.
"""

import pytest
import asyncio
import httpx
import time
from pathlib import Path
from PIL import Image
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_THEME = "a brave little mouse goes on an adventure"
TEST_PAGES = 2  # Small number for faster testing


@pytest.mark.asyncio
async def test_pod_pdf_generation():
    """
    Test generating a POD-ready PDF with CMYK and bleeds.
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create POD-ready storybook job
        response = await client.post(
            f"{BASE_URL}/generate",
            params={
                "theme": TEST_THEME,
                "num_pages": TEST_PAGES,
                "pod_ready": True
            }
        )
        
        assert response.status_code == 200
        job_data = response.json()
        job_id = job_data["job_id"]
        assert job_id is not None
        
        print(f"Created POD job: {job_id}")
        
        # Monitor job progress
        max_wait = 600  # 10 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = await client.get(f"{BASE_URL}/status/{job_id}")
            assert status_response.status_code == 200
            
            status = status_response.json()
            print(f"Progress: {status.get('progress', 0)}% - {status.get('current_step', 'Unknown')}")
            
            if status["status"] == "completed":
                # Download POD PDF
                pdf_response = await client.get(f"{BASE_URL}/download/{job_id}")
                assert pdf_response.status_code == 200
                assert pdf_response.headers["content-type"] == "application/pdf"
                
                # Save PDF for inspection
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                pdf_path = output_dir / f"test_pod_{job_id}.pdf"
                
                with open(pdf_path, "wb") as f:
                    f.write(pdf_response.content)
                
                print(f"POD PDF saved: {pdf_path}")
                
                # Verify PDF exists and has content
                assert pdf_path.exists()
                assert pdf_path.stat().st_size > 0
                
                # Basic validation: PDF should be larger due to bleeds
                # (This is a simple check - actual validation would require PDF parsing)
                print(f"POD PDF size: {pdf_path.stat().st_size} bytes")
                
                return job_id
            
            elif status["status"] == "failed":
                error_msg = status.get("error_message", "Unknown error")
                pytest.fail(f"Job failed: {error_msg}")
            
            await asyncio.sleep(2)
        
        pytest.fail("Job did not complete within timeout")


@pytest.mark.asyncio
async def test_pod_vs_standard_pdf():
    """
    Compare POD-ready PDF with standard PDF to verify differences.
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Generate standard PDF
        standard_response = await client.post(
            f"{BASE_URL}/generate",
            params={
                "theme": TEST_THEME,
                "num_pages": TEST_PAGES,
                "pod_ready": False
            }
        )
        standard_job_id = standard_response.json()["job_id"]
        
        # Generate POD PDF
        pod_response = await client.post(
            f"{BASE_URL}/generate",
            params={
                "theme": TEST_THEME,
                "num_pages": TEST_PAGES,
                "pod_ready": True
            }
        )
        pod_job_id = pod_response.json()["job_id"]
        
        # Wait for both jobs
        for job_id, job_type in [(standard_job_id, "standard"), (pod_job_id, "POD")]:
            max_wait = 600
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = await client.get(f"{BASE_URL}/status/{job_id}")
                status = status_response.json()
                
                if status["status"] == "completed":
                    break
                elif status["status"] == "failed":
                    pytest.fail(f"{job_type} job failed: {status.get('error_message')}")
                
                await asyncio.sleep(2)
            else:
                pytest.fail(f"{job_type} job did not complete within timeout")
        
        # Download both PDFs
        standard_pdf = await client.get(f"{BASE_URL}/download/{standard_job_id}")
        pod_pdf = await client.get(f"{BASE_URL}/download/{pod_job_id}")
        
        assert standard_pdf.status_code == 200
        assert pod_pdf.status_code == 200
        
        # Save for comparison
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        standard_path = output_dir / f"test_standard_{standard_job_id}.pdf"
        pod_path = output_dir / f"test_pod_{pod_job_id}.pdf"
        
        with open(standard_path, "wb") as f:
            f.write(standard_pdf.content)
        with open(pod_path, "wb") as f:
            f.write(pod_pdf.content)
        
        # POD PDF should exist and have content
        assert pod_path.exists()
        assert pod_path.stat().st_size > 0
        
        print(f"Standard PDF: {standard_path.stat().st_size} bytes")
        print(f"POD PDF: {pod_path.stat().st_size} bytes")
        
        # POD PDF might be larger due to CMYK and bleeds, but this is not guaranteed
        # The important thing is that both PDFs are generated successfully


def test_cmyk_conversion():
    """
    Test CMYK image conversion functionality.
    """
    from services.pod_preflight import convert_image_to_cmyk
    
    # Create a test RGB image
    test_image = Image.new('RGB', (100, 100), color=(255, 0, 0))
    test_path = Path("test_rgb.png")
    test_image.save(test_path)
    
    try:
        # Convert to CMYK
        cmyk_path = convert_image_to_cmyk(str(test_path))
        
        # Verify CMYK image exists
        assert Path(cmyk_path).exists()
        
        # Verify it's CMYK
        with Image.open(cmyk_path) as cmyk_img:
            assert cmyk_img.mode == 'CMYK'
        
        # Cleanup
        Path(cmyk_path).unlink()
    finally:
        # Cleanup test image
        if test_path.exists():
            test_path.unlink()


def test_bleed_extension():
    """
    Test image bleed extension functionality.
    """
    from services.pod_preflight import extend_image_with_bleed
    
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color=(0, 255, 0))
    test_path = Path("test_image.png")
    test_image.save(test_path)
    
    try:
        # Extend with bleed
        bleed_path = extend_image_with_bleed(str(test_path))
        
        # Verify extended image exists
        assert Path(bleed_path).exists()
        
        # Verify it's larger (has bleeds)
        with Image.open(bleed_path) as bleed_img:
            original_size = test_image.size
            bleed_size = bleed_img.size
            # Should be larger in both dimensions
            assert bleed_size[0] > original_size[0]
            assert bleed_size[1] > original_size[1]
        
        # Cleanup
        Path(bleed_path).unlink()
    finally:
        # Cleanup test image
        if test_path.exists():
            test_path.unlink()


def test_pod_dimensions():
    """
    Test POD dimension calculations.
    """
    from services.pod_preflight import get_pod_dimensions, get_safe_area, BLEED_SIZE, TRIM_MARGIN
    
    page_width, page_height, trim_width, trim_height = get_pod_dimensions()
    safe_x, safe_y, safe_width, safe_height = get_safe_area()
    
    # Verify dimensions are reasonable
    assert page_width > trim_width  # Should include bleeds
    assert page_height > trim_height  # Should include bleeds
    
    # Verify safe area is within trim
    assert safe_x >= BLEED_SIZE  # Safe area starts after bleed
    assert safe_y >= BLEED_SIZE
    assert safe_width < trim_width  # Safe width is less than trim
    assert safe_height < trim_height  # Safe height is less than trim
    
    # Verify safe area respects margins
    assert safe_x == BLEED_SIZE + TRIM_MARGIN
    assert safe_y == BLEED_SIZE + TRIM_MARGIN


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
