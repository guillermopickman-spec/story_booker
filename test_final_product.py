"""
Final Product Test - Complete Storybook Generation
Tests all functionality end-to-end with authenticated Pollinations API.
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.main import jobs, process_storybook_job
from services.image_storage import list_job_images, get_job_images_by_beat
from dotenv import load_dotenv
import uuid
import logging

load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def display_final_results(job_id: str):
    """Display comprehensive final results."""
    print("\n" + "="*80)
    print("FINAL TEST RESULTS")
    print("="*80)
    
    if job_id in jobs:
        job = jobs[job_id]
        print(f"\nJob ID: {job_id}")
        print(f"Status: {job.status}")
        print(f"Final Progress: {job.progress}%")
        
        if job.error_message:
            print(f"\n[ERROR] {job.error_message[:500]}...")
        
        if job.file_path:
            pdf_path = Path(job.file_path)
            if pdf_path.exists():
                pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
                pdf_size_kb = pdf_path.stat().st_size / 1024
                print(f"\n[SUCCESS] PDF GENERATED!")
                print(f"  Filename: {pdf_path.name}")
                print(f"  Full Path: {pdf_path.resolve()}")
                print(f"  Size: {pdf_size_mb:.2f} MB ({pdf_size_kb:.1f} KB)")
            else:
                print(f"\n[ERROR] PDF file not found: {job.file_path}")
        else:
            print(f"\n[ERROR] PDF file path not set")
    
    png_files = list_job_images(job_id)
    images_by_beat = get_job_images_by_beat(job_id)
    
    print(f"\nGenerated {len(png_files)} PNG images")
    if images_by_beat:
        print("\nImages by Story Beat:")
        for beat_num in sorted(images_by_beat.keys()):
            beat_images = images_by_beat[beat_num]
            print(f"  Beat {beat_num}: {len(beat_images)} image(s)")
    
    print("="*80)


async def test_final_product():
    """Run complete end-to-end test."""
    from src.models import JobStatus
    
    print("="*80)
    print("STORY BOOKER - FINAL PRODUCT TEST")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify API keys are configured
    api_key = os.getenv("POLLINATIONS_API_KEY", "")
    placeholder_values = ["your_pollinations_api_key_here", "your_api_key_here", ""]
    has_valid_key = api_key and api_key.strip().lower() not in [p.lower() for p in placeholder_values]
    
    if not has_valid_key:
        print("[ERROR] POLLINATIONS_API_KEY is required!")
        print("Free tier is no longer supported.")
        print("Please set a valid API key in your .env file.")
        print("Get your API key at: https://enter.pollinations.ai")
        return False
    
    print("[INFO] Using authenticated Pollinations API")
    print(f"[INFO] API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '***'}")
    print()
    
    jobs.clear()
    
    theme = "a brave little mouse goes on a magical adventure"
    num_pages = 2
    job_id = str(uuid.uuid4())
    
    print(f"Theme: '{theme}'")
    print(f"Pages: {num_pages}")
    print(f"Job ID: {job_id}")
    print()
    print(f"PDF Export Name: {job_id}.pdf")
    print(f"PDF Location: {Path('output').resolve() / f'{job_id}.pdf'}")
    print()
    print("Starting complete storybook generation...")
    print("This will test:")
    print("  - Story generation (Author Agent)")
    print("  - Image prompt generation (Art Director Agent)")
    print("  - Image generation (Authenticated Pollinations API)")
    print("  - Background removal & processing")
    print("  - PDF compilation")
    print("-" * 80)
    
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        file_path=None,
        progress=0,
        error_message=None,
        current_step=None
    )
    
    start_time = time.time()
    task = asyncio.create_task(process_storybook_job(job_id, theme, num_pages))
    
    last_progress = -1
    last_status = None
    iteration = 0
    max_wait = 600  # 10 minutes
    
    while time.time() - start_time < max_wait:
        iteration += 1
        await asyncio.sleep(2)
        
        if job_id in jobs:
            job = jobs[job_id]
            progress = job.progress or 0
            status = job.status
            current_step = job.current_step or ""
            elapsed = int(time.time() - start_time)
            
            # Print updates
            if iteration <= 5 or progress != last_progress or status != last_status or elapsed % 15 == 0:
                status_icon = "[...]" if status == "processing" else "[OK]" if status == "completed" else "[ERR]" if status == "failed" else "[...]"
                print(f"{status_icon} [{elapsed:3d}s] {progress:3d}% | {status:12s} | {current_step[:70]}")
                last_progress = progress
                last_status = status
            
            if status == "completed":
                elapsed_total = int(time.time() - start_time)
                await task
                
                print("\n" + "="*80)
                print("[SUCCESS] TEST COMPLETED!")
                print("="*80)
                print(f"Total Time: {elapsed_total}s ({elapsed_total//60}m {elapsed_total%60}s)")
                print()
                
                display_final_results(job_id)
                
                # Final summary
                pdf_path = Path(job.file_path) if job.file_path else Path("output") / f"{job_id}.pdf"
                print("\n" + "="*80)
                print("TEST SUMMARY")
                print("="*80)
                print("[PASS] All functionality tests PASSED!")
                print()
                print("PDF EXPORT INFORMATION:")
                print(f"  Filename: {pdf_path.name}")
                print(f"  Full Path: {pdf_path.resolve()}")
                if pdf_path.exists():
                    print(f"  Size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
                print()
                print("To view your storybook, open:")
                print(f"  {pdf_path.resolve()}")
                print("="*80)
                
                return True
                
            elif status == "failed":
                elapsed_total = int(time.time() - start_time)
                await task
                
                print("\n" + "="*80)
                print("[FAILED] TEST FAILED!")
                print("="*80)
                print(f"Total Time: {elapsed_total}s")
                print()
                display_final_results(job_id)
                return False
    
    print(f"\n[TIMEOUT] Test timed out after {int(time.time() - start_time)}s")
    display_final_results(job_id)
    return False


if __name__ == "__main__":
    try:
        print("\n[INFO] Final Product Test")
        print("[INFO] This test generates a complete 2-page storybook")
        print("[INFO] Using authenticated Pollinations API (enter.pollinations.ai)")
        print("[INFO] Estimated time: 3-5 minutes\n")
        
        success = asyncio.run(test_final_product())
        
        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success:
            print("\n[SUCCESS] Final product test PASSED!")
            sys.exit(0)
        else:
            print("\n[FAILED] Final product test FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
