"""
FastAPI application for Story Booker - AI Sticker-Book Generator.
"""

import os
import uuid
import asyncio
import traceback
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from src.models import JobStatus
from services.author_agent import generate_storybook as generate_storybook_content
from services.art_director_agent import generate_image_prompts
from services.sticker_generator import generate_stickers_for_beat
from services.pdf_generator import generate_pdf
from services.image_service import get_image_service
from services.llm_client import get_llm_client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Story Booker API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, JobStatus] = {}


async def process_storybook_job(job_id: str, theme: str = None, num_pages: int = 5):
    """
    Background task to process a storybook generation job.
    
    Executes phases sequentially:
    1. Phase 2a: Generate storybook
    2. Phase 2b: Generate image prompts for each beat
    3. Phase 3: Generate stickers for each beat
    4. Phase 4: Generate PDF
    
    Args:
        job_id: Unique job identifier
        theme: Optional theme for the storybook
        num_pages: Number of pages/beats to generate (default: 5)
    """
    try:
        if job_id in jobs:
            jobs[job_id].status = "processing"
            jobs[job_id].progress = 0
            jobs[job_id].current_step = "Initializing"
        
        llm_client = get_llm_client()
        image_service = get_image_service()
        
        if job_id in jobs:
            jobs[job_id].current_step = "Generating story"
            jobs[job_id].progress = 5
        
        storybook = await generate_storybook_content(
            theme=theme or "adventure",
            num_pages=num_pages,
            llm_client=llm_client
        )
        
        if job_id in jobs:
            jobs[job_id].progress = 10
            jobs[job_id].current_step = "Story generated"
        
        all_image_prompts = {}
        total_beats = len(storybook.beats)
        
        for i, beat in enumerate(storybook.beats, 1):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating image prompts for beat {i}/{total_beats}"
                progress = int(10 + (20 * (i - 1) / total_beats))
                jobs[job_id].progress = progress
            
            image_prompts = await generate_image_prompts(
                beat=beat,
                llm_client=llm_client
            )
            all_image_prompts[i] = image_prompts
        
        if job_id in jobs:
            jobs[job_id].progress = 30
            jobs[job_id].current_step = "Image prompts generated"
        
        image_paths = {}
        
        for i, beat in enumerate(storybook.beats, 1):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating stickers for beat {i}/{total_beats}"
                progress = int(30 + (30 * (i - 1) / total_beats))
                jobs[job_id].progress = progress
            
            prompts = all_image_prompts.get(i, [])
            if prompts:
                beat_image_paths = await generate_stickers_for_beat(
                    prompts=prompts,
                    job_id=job_id,
                    beat_num=i,
                    image_service=image_service
                )
                image_paths[i] = beat_image_paths
        
        if job_id in jobs:
            jobs[job_id].progress = 60
            jobs[job_id].current_step = "Stickers generated"
        
        if job_id in jobs:
            jobs[job_id].current_step = "Generating PDF"
            jobs[job_id].progress = 70
        
        pdf_path = generate_pdf(
            storybook=storybook,
            job_id=job_id,
            image_paths=image_paths
        )
        
        if job_id in jobs:
            jobs[job_id].status = "completed"
            jobs[job_id].file_path = pdf_path
            jobs[job_id].progress = 100
            jobs[job_id].current_step = "Completed"
    
    except asyncio.TimeoutError as e:
        error_msg = f"Operation timed out: {str(e)}"
        full_traceback = traceback.format_exc()
        complete_error = f"{error_msg}\n\nTraceback:\n{full_traceback}"
        
        logger.error(f"Job {job_id} timed out: {error_msg}")
        logger.debug(f"Full traceback for job {job_id}:\n{full_traceback}")
        
        if job_id in jobs:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = complete_error
            jobs[job_id].current_step = "Failed: Timeout"
    except Exception as e:
        error_msg = f"Error processing job: {str(e)}"
        full_traceback = traceback.format_exc()
        complete_error = f"{error_msg}\n\nTraceback:\n{full_traceback}"
        
        logger.error(f"Job {job_id} failed: {error_msg}")
        logger.debug(f"Full traceback for job {job_id}:\n{full_traceback}")
        
        if job_id in jobs:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = complete_error
            jobs[job_id].current_step = f"Failed: {type(e).__name__}"


@app.post("/generate")
async def generate_storybook(theme: str = None, num_pages: int = 5, background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Create a new storybook generation job.
    
    Args:
        theme: Optional theme for the storybook
        num_pages: Number of pages/beats to generate (default: 5, min: 1, max: 10)
        background_tasks: FastAPI BackgroundTasks instance
        
    Returns:
        Dictionary with job_id
    """
    if num_pages < 1 or num_pages > 10:
        raise HTTPException(
            status_code=400, 
            detail="num_pages must be between 1 and 10"
        )
    
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        file_path=None,
        progress=0,
        error_message=None,
        current_step=None
    )
    
    background_tasks.add_task(process_storybook_job, job_id, theme, num_pages)
    
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a storybook generation job.
    
    Args:
        job_id: The unique identifier for the job
        
    Returns:
        JobStatus object with current status and progress
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.get("/download/{job_id}")
async def download_storybook(job_id: str):
    """
    Download the generated PDF for a completed job.
    
    Args:
        job_id: The unique identifier for the job
        
    Returns:
        PDF file response
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(
            status_code=404, 
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    if not job.file_path:
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        job.file_path,
        media_type="application/pdf",
        filename=f"storybook_{job_id}.pdf"
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Story Booker API",
        "version": "0.0.1",
        "description": "AI Sticker-Book Generator"
    }
