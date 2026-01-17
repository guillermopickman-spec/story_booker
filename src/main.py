"""
FastAPI application for Story Booker - AI Sticker-Book Generator.
"""

import os
import uuid
import asyncio
import traceback
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from io import BytesIO
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from PIL import Image as PILImage

from src.models import JobStatus, Character, StoryBeat, ImagePrompt
from services.author_agent import generate_storybook as generate_storybook_content
from services.art_director_agent import generate_image_prompts
# Sticker generation no longer used - using full-page images instead
from services.pdf_generator import generate_pdf
from services.image_service import get_image_service
from services.llm_client import get_llm_client
from services.character_service import extract_main_characters, generate_characters_reference, generate_character_reference_image, match_character_to_subject, ensure_characters_in_beats
from services.art_director_agent import apply_style_to_prompt
from services.image_storage import ensure_job_directory
from services.pdf_storage import get_pdf_path, pdf_exists

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Story Booker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, JobStatus] = {}


async def process_storybook_job(job_id: str, theme: Optional[str] = None, num_pages: int = 5, style: Optional[str] = None, languages: Optional[List[str]] = None, pod_ready: bool = False):
    """
    Background task to process a storybook generation job.
    
    Executes phases sequentially:
    1. Generate storybook in first language (for image generation)
    2. Generate images (language-agnostic, shared across all languages)
    3. For each language: Generate storybook content and create PDF
    
    Args:
        job_id: Unique job identifier
        theme: Optional theme for the storybook
        num_pages: Number of pages/beats to generate (default: 5)
        style: Optional art style name (CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART)
        languages: List of languages for story generation (default: ["en"]). Generates one PDF per language.
        pod_ready: If True, generate POD-ready PDF with CMYK colors and bleeds
    """
    # Get default style from environment if not provided
    if style is None:
        style = os.getenv("DEFAULT_ART_STYLE", "3D_RENDERED")
    
    # Get default languages (default to English)
    if languages is None or len(languages) == 0:
        languages = ["en"]
    
    # Remove duplicates while preserving order
    languages = list(dict.fromkeys(languages))
    llm_client = None
    try:
        if job_id in jobs:
            jobs[job_id].status = "processing"
            jobs[job_id].progress = 0
            jobs[job_id].current_step = "Initializing"
        
        llm_client = get_llm_client()
        image_service = get_image_service()
        
        # Step 1: Generate story in first language (for image generation)
        first_language = languages[0]
        if job_id in jobs:
            jobs[job_id].current_step = f"Generating story in {first_language} (for images)"
            jobs[job_id].progress = 5
        
        base_storybook = await generate_storybook_content(
            theme=theme or "adventure",
            num_pages=num_pages,
            language=first_language,
            llm_client=llm_client
        )
        
        if job_id in jobs:
            jobs[job_id].progress = 10
            jobs[job_id].current_step = "Base story generated"
        
        # Generate cover image (using base storybook)
        if job_id in jobs:
            jobs[job_id].current_step = "Generating cover image"
            jobs[job_id].progress = 11
        
        cover_image_path = None
        try:
            # Create cover image prompt based on title and first beat
            # Note: Title will be overlaid in PDF, so exclude text from image
            first_beat = base_storybook.beats[0] if base_storybook.beats else None
            if first_beat:
                cover_prompt = f"Children's book cover illustration scene: {first_beat.visual_description}, hero scene, exciting and colorful, full page illustration, no text, no words, no letters, illustration only, visual scene without any written text"
            else:
                cover_prompt = f"Children's book cover illustration scene: exciting adventure scene, colorful and engaging, full page illustration, no text, no words, no letters, illustration only, visual scene without any written text"
            
            # Apply style to cover prompt
            cover_prompt = apply_style_to_prompt(cover_prompt, style)
            
            # Generate cover image
            raw_cover_image = await image_service.generate_image(
                prompt=cover_prompt,
                size="1024x1024"
            )
            
            # Process cover image (resize for full-page cover)
            with PILImage.open(BytesIO(raw_cover_image)) as cover_img:
                # Resize to a good cover size (maintain aspect ratio, but make it suitable for full page)
                cover_img = cover_img.convert('RGB')
                # For cover, we want a full-page image, so resize to page dimensions
                # US Letter: 8.5" x 11" = 612pt x 792pt (at 72 DPI)
                # Use 2x resolution for better quality
                PAGE_WIDTH = 612
                PAGE_HEIGHT = 792
                cover_width = int(PAGE_WIDTH * 2)  # Higher resolution for quality
                cover_height = int(PAGE_HEIGHT * 2)
                cover_img = cover_img.resize((cover_width, cover_height), PILImage.Resampling.LANCZOS)
                
                # Save cover image
                assets_dir = ensure_job_directory(job_id)
                cover_path = assets_dir / "cover.png"
                cover_img.save(cover_path, format='PNG', optimize=True)
                cover_image_path = str(cover_path)
                logger.info(f"Cover image generated: {cover_image_path}")
        except Exception as e:
            logger.warning(f"Failed to generate cover image: {e}. Continuing without cover.")
            cover_image_path = None
        
        # Extract main characters for character consistency (using base storybook)
        if job_id in jobs:
            jobs[job_id].current_step = "Extracting main characters"
            jobs[job_id].progress = 12
        
        characters = []
        try:
            characters = await extract_main_characters(
                theme=theme or "adventure",
                storybook=base_storybook,
                language=first_language,
                llm_client=llm_client
            )
            if characters:
                base_storybook.characters = characters
                logger.info(f"Extracted {len(characters)} character(s): {', '.join(c.name for c in characters)}")
                
                # Ensure main characters appear in beats when mentioned
                ensure_characters_in_beats(base_storybook, characters)
                logger.info("Ensured main characters appear in sticker subjects when mentioned in story")
                
                # Generate reference images for all characters (base design)
                if job_id in jobs:
                    jobs[job_id].current_step = "Generating character reference images"
                    jobs[job_id].progress = 14
                
                for i, character in enumerate(characters):
                    try:
                        reference_image_path, seed = await generate_character_reference_image(
                            character=character,
                            job_id=job_id,
                            image_service=image_service
                        )
                        character.reference_image_path = reference_image_path
                        character.seed = seed
                        logger.info(f"Character reference image generated for {character.name}: {reference_image_path}, seed: {seed}")
                    except Exception as e:
                        logger.warning(f"Failed to generate character reference image for {character.name}: {e}. Continuing without visual reference.")
                        character.reference_image_path = None
                        character.seed = None
            else:
                logger.info("No main characters identified")
                base_storybook.characters = []
        except Exception as e:
            logger.warning(f"Failed to extract characters: {e}. Continuing without character consistency.")
            base_storybook.characters = []
        
        # Generate images once (shared across all languages)
        all_image_prompts = {}
        all_background_prompts = {}
        total_beats = len(base_storybook.beats)
        
        # Generate character references for Art Director
        character_reference = generate_characters_reference(base_storybook.characters) if base_storybook.characters else None
        character_reference_image_paths = [char.reference_image_path for char in base_storybook.characters if char.reference_image_path]
        character_reference_image_path = ", ".join(character_reference_image_paths) if character_reference_image_paths else None
        
        for i, beat in enumerate(base_storybook.beats, 1):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating image prompts for beat {i}/{total_beats}"
                progress = int(14 + (16 * (i - 1) / total_beats))
                jobs[job_id].progress = progress
            
            image_prompts, background_prompt = await generate_image_prompts(
                beat=beat,
                character_reference=character_reference,
                character_reference_image_path=character_reference_image_path,
                characters=base_storybook.characters,
                style=style,
                llm_client=llm_client
            )
            all_image_prompts[i] = image_prompts
            all_background_prompts[i] = background_prompt
        
        if job_id in jobs:
            jobs[job_id].progress = 30
            jobs[job_id].current_step = "Image prompts generated"
        
        image_paths = {}  # Changed to Dict[int, str] - single full-page image per beat
        
        for i, beat in enumerate(base_storybook.beats, 1):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating full-page image for beat {i}/{total_beats}"
                progress = int(30 + (30 * (i - 1) / total_beats))
                jobs[job_id].progress = progress
            
            # Generate full-page scene image using background prompt
            background_prompt = all_background_prompts.get(i)
            if background_prompt:
                try:
                    # Enhance prompt for full-page scene
                    fullpage_prompt = background_prompt.prompt
                    if "full-page" not in fullpage_prompt.lower() and "full page" not in fullpage_prompt.lower():
                        fullpage_prompt = f"Full-page children's book illustration scene: {fullpage_prompt}, complete scene, full page illustration, no white space, vibrant colors"
                    
                    # Further enhance with explicit character species if characters exist
                    if base_storybook.characters:
                        beat = base_storybook.beats[i - 1]  # i is 1-indexed
                        beat_text_lower = beat.text.lower()
                        beat_visual_lower = beat.visual_description.lower()
                        
                        # Build character reinforcement string
                        character_reinforcements = []
                        for char in base_storybook.characters:
                            char_name_lower = char.name.lower()
                            char_species_lower = char.species.lower() if char.species else None
                            
                            # Check if character is mentioned in this beat
                            if (char_name_lower in beat_text_lower or char_name_lower in beat_visual_lower or
                                (char_species_lower and (char_species_lower in beat_text_lower or char_species_lower in beat_visual_lower))):
                                
                                # Build explicit character description
                                char_desc = []
                                if char.species:
                                    char_desc.append(f"{char.name} is a {char.species} character")
                                else:
                                    char_desc.append(f"{char.name}")
                                
                                if char.key_features:
                                    char_desc.append(f"with {', '.join(char.key_features[:2])}")
                                
                                if char.color_palette:
                                    primary = char.color_palette.get("primary_color") or char.color_palette.get("skin_color")
                                    if primary:
                                        char_desc.append(f"{primary} colored")
                                
                                if char_desc:
                                    character_reinforcements.append(" ".join(char_desc))
                        
                        # Add character reinforcement to prompt if characters are mentioned
                        if character_reinforcements:
                            char_info = ". ".join(character_reinforcements)
                            # Add explicit instruction to preserve species
                            fullpage_prompt = f"{fullpage_prompt}. CRITICAL: Characters in scene must appear with correct species: {char_info}. Do NOT change character species (if a character is a mouse, it must stay a mouse; if a character is a bear, it must stay a bear, etc.)."
                    
                    # Generate full-page scene image
                    raw_image_data = await image_service.generate_image(
                        prompt=fullpage_prompt,
                        size="1024x1024"
                    )
                    
                    # Save full-page image
                    assets_dir = ensure_job_directory(job_id)
                    fullpage_filename = f"beat_{i}_fullpage.png"
                    fullpage_path = assets_dir / fullpage_filename
                    
                    with open(fullpage_path, 'wb') as f:
                        f.write(raw_image_data)
                    
                    # Ensure RGB mode
                    with PILImage.open(fullpage_path) as saved_img:
                        if saved_img.mode != 'RGB':
                            rgb_img = saved_img.convert('RGB')
                            rgb_img.save(fullpage_path, format='PNG', optimize=True)
                    
                    image_paths[i] = str(fullpage_path)
                    logger.info(f"Full-page image generated for beat {i}: {image_paths[i]}")
                except Exception as e:
                    logger.warning(f"Failed to generate full-page image for beat {i}: {e}. Continuing without image.")
                    image_paths[i] = None
            else:
                logger.warning(f"No background prompt for beat {i}. Skipping image generation.")
                image_paths[i] = None
        
        if job_id in jobs:
            jobs[job_id].progress = 60
            jobs[job_id].current_step = "Full-page images generated"
        
        # Generate PDFs for each language
        file_paths = {}
        total_languages = len(languages)
        
        for lang_idx, language in enumerate(languages):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating PDF in {language} ({lang_idx + 1}/{total_languages})"
                progress = int(70 + (25 * lang_idx / total_languages))
                jobs[job_id].progress = progress
            
            # Generate storybook content in this language
            storybook = await generate_storybook_content(
                theme=theme or "adventure",
                num_pages=num_pages,
                language=language,
                llm_client=llm_client
            )
            
            # Use the same images and cover for all languages
            storybook.cover_image_path = cover_image_path
            storybook.characters = base_storybook.characters  # Use same characters
            
            # Generate PDF for this language
            pdf_path = generate_pdf(
                storybook=storybook,
                job_id=job_id,
                image_paths=image_paths,
                cover_image_path=cover_image_path,
                synopsis=storybook.synopsis,
                language=language,
                pod_ready=pod_ready
            )
            
            file_paths[language] = pdf_path
            logger.info(f"PDF generated for language {language}: {pdf_path}")
        
        if job_id in jobs:
            jobs[job_id].status = "completed"
            jobs[job_id].file_paths = file_paths
            # Set primary file_path to first language's PDF for backward compatibility
            jobs[job_id].file_path = file_paths.get(languages[0]) if file_paths else None
            jobs[job_id].progress = 100
            jobs[job_id].current_step = f"Completed ({total_languages} language(s))"
    
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
    finally:
        # Cleanup async clients to allow process to exit cleanly
        if llm_client is not None:
            try:
                await llm_client.close()
            except Exception as e:
                logger.warning(f"Error closing LLM client: {e}")


@app.post("/generate")
async def generate_storybook(
    theme: Optional[str] = None, 
    num_pages: int = 5, 
    style: Optional[str] = None,
    languages: Optional[List[str]] = None,
    pod_ready: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create a new storybook generation job.
    
    Args:
        theme: Optional theme for the storybook
        num_pages: Number of pages/beats to generate (default: 5, min: 1, max: 10)
        style: Optional art style name (CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART)
        languages: List of languages for story generation (default: ["en"]). Can specify multiple languages like ["en", "es"] to generate the same book in multiple languages.
        pod_ready: If True, generate POD-ready PDF with CMYK colors and 0.125" bleeds for Amazon KDP
        background_tasks: FastAPI BackgroundTasks instance
        
    Returns:
        Dictionary with job_id
    """
    if num_pages < 1 or num_pages > 10:
        raise HTTPException(
            status_code=400, 
            detail="num_pages must be between 1 and 10"
        )
    
    # Default to English if no languages specified
    if languages is None:
        languages = ["en"]
    
    # Validate languages parameter
    valid_languages = ["en", "es"]
    invalid_languages = [lang for lang in languages if lang not in valid_languages]
    if invalid_languages:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid languages: {invalid_languages}. Supported languages: {valid_languages}'
        )
    
    # Remove duplicates while preserving order
    languages = list(dict.fromkeys(languages))
    
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        file_path=None,
        file_paths=None,
        progress=0,
        error_message=None,
        current_step=None
    )
    
    background_tasks.add_task(process_storybook_job, job_id, theme, num_pages, style, languages, pod_ready)
    
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
async def download_storybook(job_id: str, language: Optional[str] = None):
    """
    Download the generated PDF for a completed job.
    
    Args:
        job_id: The unique identifier for the job
        language: Optional language code to select specific language PDF (default: first language)
        
    Returns:
        PDF file response
    """
    # Check if job exists in memory, otherwise try to find PDF file directly on disk
    pdf_path = None
    
    if job_id in jobs:
        # Job exists in memory - use its stored file paths
        job = jobs[job_id]
        
        if job.status != "completed":
            raise HTTPException(
                status_code=404, 
                detail=f"Job is not completed. Current status: {job.status}"
            )
        
        # Determine which PDF file to return
        if language and job.file_paths:
            pdf_path = job.file_paths.get(language)
        
        if not pdf_path:
            pdf_path = job.file_path
    else:
        # Job not in memory (likely after restart) - check if PDF file exists on disk
        # Try to find PDF file on disk
        if language:
            pdf_path_obj = get_pdf_path(job_id, language)
            if pdf_path_obj.exists():
                pdf_path = str(pdf_path_obj.absolute())
        
        # If language-specific not found, try default
        if not pdf_path:
            pdf_path_obj = get_pdf_path(job_id)
            if pdf_path_obj.exists():
                pdf_path = str(pdf_path_obj.absolute())
    
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    response = FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"storybook_{job_id}{f'_{language}' if language else ''}.pdf",
        headers={
            "Content-Disposition": f'inline; filename="storybook_{job_id}{f"_{language}" if language else ""}.pdf"',
            "X-Content-Type-Options": "nosniff",
        }
    )
    return response


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Story Booker API",
        "version": "0.1.0",
        "description": "AI Sticker-Book Generator"
    }
