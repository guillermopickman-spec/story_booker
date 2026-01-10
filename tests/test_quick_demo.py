"""
Quick Demo Test - Uses mock providers for fast demonstration.
Shows all functionality working end-to-end.
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import jobs, process_storybook_job
from services.image_storage import list_job_images, get_job_images_by_beat
from dotenv import load_dotenv

load_dotenv(override=True)


def display_results(job_id: str):
    """Display comprehensive results."""
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    if job_id in jobs:
        job = jobs[job_id]
        print(f"\nJob ID: {job_id}")
        print(f"Status: {job.status}")
        print(f"Final Progress: {job.progress}%")
        
        if job.file_path:
            pdf_path = Path(job.file_path)
            if pdf_path.exists():
                pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"\n[SUCCESS] PDF GENERATED!")
                print(f"          File: {pdf_path.resolve()}")
                print(f"          Size: {pdf_size_mb:.2f} MB")
        
        png_files = list_job_images(job_id)
        images_by_beat = get_job_images_by_beat(job_id)
        
        print(f"\nPNG Images Generated: {len(png_files)}")
        if images_by_beat:
            for beat_num in sorted(images_by_beat.keys()):
                beat_images = images_by_beat[beat_num]
                print(f"  Beat {beat_num}: {len(beat_images)} image(s)")
    
    print("="*80)


async def main():
    """Run quick demo with mock providers."""
    import uuid
    from src.models import JobStatus
    
    print("="*80)
    print("QUICK DEMO - MOCK PROVIDERS")
    print("="*80)
    print()
    
    # Force mock providers for quick demo
    os.environ["USE_MOCK_PROVIDER"] = "true"
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["IMAGE_PROVIDER"] = "mock"
    
    jobs.clear()
    
    theme = "a brave little mouse goes on an adventure"
    num_pages = 2
    job_id = str(uuid.uuid4())
    
    print(f"Theme: '{theme}'")
    print(f"Pages: {num_pages}")
    print(f"Job ID: {job_id}")
    print("\nStarting...")
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
    
    # Monitor progress
    while True:
        await asyncio.sleep(1)
        if job_id in jobs:
            job = jobs[job_id]
            progress = job.progress or 0
            status = job.status
            current_step = job.current_step or ""
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed:3d}s] {progress:3d}% | {status:12s} | {current_step}")
            
            if status == "completed":
                elapsed_total = int(time.time() - start_time)
                print(f"\nCompleted in {elapsed_total}s!")
                await task
                display_results(job_id)
                return True
            elif status == "failed":
                print(f"\nFailed: {job.error_message}")
                await task
                return False
        
        if time.time() - start_time > 120:  # 2 minute timeout
            print("\nTimeout!")
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n[SUCCESS] Demo completed! Check the output folder for the PDF.")
        else:
            print("\n[FAILED] Demo failed.")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
