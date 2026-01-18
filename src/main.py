"""
FastAPI application for Story Booker - AI Sticker-Book Generator.
"""

import os
import uuid
import json
import asyncio
import traceback
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from io import BytesIO
from functools import partial
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from PIL import Image as PILImage

from src.models import JobStatus, Character, StoryBeat, ImagePrompt, CharacterMetadata
from services.author_agent import generate_storybook as generate_storybook_content
from services.art_director_agent import generate_image_prompts
# Sticker generation no longer used - using full-page images instead
from services.pdf_generator import generate_pdf
from services.image_service import get_image_service
from services.llm_client import get_llm_client
from services.character_service import extract_main_characters, generate_characters_reference, generate_character_reference_image, match_character_to_subject, ensure_characters_in_beats, create_refined_character_prompt, match_characters_by_similarity
from services.art_director_agent import apply_style_to_prompt
from services.image_storage import ensure_job_directory
from services.pdf_storage import get_pdf_path, pdf_exists
from services.character_storage import (
    ensure_characters_directory, get_character_folder_path, character_exists,
    load_character, save_character, delete_character, list_characters,
    get_character_image_path, dict_to_character, sanitize_character_id
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Story Booker API", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, JobStatus] = {}


async def process_storybook_job(job_id: str, theme: Optional[str] = None, num_pages: int = 5, style: Optional[str] = None, languages: Optional[List[str]] = None, pod_ready: bool = False, character_ids: Optional[List[str]] = None):
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
        logger.info(f"Image service initialized with provider: {image_service.provider if hasattr(image_service, 'provider') else 'unknown'}")
        
        # Load characters from storage FIRST (before story generation) if provided
        # This allows the author agent to incorporate selected characters into the story
        stored_characters = []
        if character_ids:
            if job_id in jobs:
                jobs[job_id].current_step = "Loading selected characters"
                jobs[job_id].progress = 5
            for char_id in character_ids:
                try:
                    char_data = load_character(char_id)
                    if char_data:
                        character = dict_to_character(char_data)
                        # Set reference image path if it exists
                        image_path = get_character_image_path(char_id)
                        if image_path:
                            character.reference_image_path = str(image_path)
                        stored_characters.append(character)
                        logger.info(f"Loaded character from storage: {character.name} (ID: {char_id})")
                except Exception as e:
                    logger.warning(f"Failed to load character {char_id}: {e}. Skipping.")
        
        # Step 1: Generate story in first language (for image generation)
        # Pass stored characters to author agent so it can incorporate them into the story
        first_language = languages[0]
        if job_id in jobs:
            jobs[job_id].current_step = f"Generating story in {first_language} (for images)"
            jobs[job_id].progress = 7
        
        logger.info(f"Starting story generation - theme: {theme}, pages: {num_pages}, language: {first_language}, characters: {len(stored_characters) if stored_characters else 0}")
        # Add timeout to prevent infinite loops
        story_timeout = float(os.getenv("STORY_GENERATION_TIMEOUT", "300"))  # 5 minutes default
        try:
            base_storybook = await asyncio.wait_for(
                generate_storybook_content(
                    theme=theme or "adventure",
                    num_pages=num_pages,
                    language=first_language,
                    characters=stored_characters if stored_characters else None,  # Pass stored characters to author agent (None if empty list)
                    llm_client=llm_client
                ),
                timeout=story_timeout
            )
            logger.info(f"Story generation completed - title: {base_storybook.title if base_storybook else 'None'}, beats: {len(base_storybook.beats) if base_storybook else 0}")
        except asyncio.TimeoutError:
            error_msg = f"Story generation timed out after {story_timeout}s"
            logger.error(error_msg)
            if job_id in jobs:
                jobs[job_id].status = "error"
                jobs[job_id].error_message = error_msg
            raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Error during story generation: {e}", exc_info=True)
            if job_id in jobs:
                jobs[job_id].status = "error"
                jobs[job_id].error_message = f"Story generation failed: {str(e)}"
            raise
        
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
            logger.info(f"Generating cover image with prompt (first 200 chars): {cover_prompt[:200]}...")
            
            # Generate cover image
            logger.info("Calling image_service.generate_image for cover...")
            raw_cover_image = await image_service.generate_image(
                prompt=cover_prompt,
                size="1024x1024"
            )
            logger.info(f"Cover image generated successfully, size: {len(raw_cover_image) if raw_cover_image else 0} bytes")
            
            if not raw_cover_image:
                raise ValueError("Image service returned empty image data")
            
            # Process cover image (resize for full-page cover)
            logger.info("Processing cover image...")
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
                logger.info(f"Cover image saved successfully: {cover_image_path}")
        except Exception as e:
            logger.error(f"Failed to generate cover image: {e}", exc_info=True)
            cover_image_path = None
            # Don't fail the whole job if cover fails, but log it clearly
        
        # Extract main characters for character consistency (using base storybook)
        # This finds any characters mentioned in the story that weren't pre-selected
        if job_id in jobs:
            jobs[job_id].current_step = "Extracting main characters"
            jobs[job_id].progress = 12
        
        extracted_characters = []
        try:
            extracted_characters = await extract_main_characters(
                theme=theme or "adventure",
                storybook=base_storybook,
                language=first_language,
                llm_client=llm_client
            )
        except Exception as e:
            logger.warning(f"Failed to extract characters: {e}. Continuing with stored characters only.")
        
        # Smart merge stored and extracted characters, matching by similarity
        characters = []
        selected_character_names = set()  # Track which characters are selected from storage
        character_names = set()
        
        # Add stored characters first (they take priority and are always included)
        for char in stored_characters:
            characters.append(char)
            selected_character_names.add(char.name.lower())
            character_names.add(char.name.lower())
            logger.info(f"Added stored character: {char.name}")
        
        # Match extracted characters with stored ones by similarity (species/description/key features)
        for extracted_char in extracted_characters:
            # Try to match with stored character
            matched_stored = match_characters_by_similarity(extracted_char, stored_characters)
            
            if matched_stored:
                # Use stored character, skip extracted one
                logger.info(f"Matched extracted character '{extracted_char.name}' (species: {extracted_char.species}) with stored character '{matched_stored.name}' (species: {matched_stored.species})")
                continue
            
            # No match found - add extracted character only if not already in list
            if extracted_char.name.lower() not in character_names:
                characters.append(extracted_char)
                character_names.add(extracted_char.name.lower())
                logger.info(f"Added extracted character: {extracted_char.name} (not matching any stored character)")
            else:
                logger.info(f"Skipping extracted character '{extracted_char.name}' - already exists")
        
        if characters:
            base_storybook.characters = characters
            logger.info(f"Using {len(characters)} character(s): {', '.join(c.name for c in characters)}")
            
            # Ensure main characters appear in beats when mentioned
            # Selected characters will always appear in the first beat even if not mentioned
            ensure_characters_in_beats(base_storybook, characters, selected_character_names)
            logger.info("Ensured main characters appear in sticker subjects when mentioned in story (selected characters forced into first beat)")
            
            # Generate reference images only for extracted characters that don't match stored ones
            # Selected characters already have reference images from storage
            if job_id in jobs:
                jobs[job_id].current_step = "Generating character reference images"
                jobs[job_id].progress = 14
            
            for i, character in enumerate(characters):
                # Skip if character is selected (already has reference image from storage)
                if character.name.lower() in selected_character_names:
                    logger.info(f"Skipping reference image generation for selected character: {character.name} (already has image from storage)")
                    continue
                
                # Skip if character already has a reference image
                if character.reference_image_path and Path(character.reference_image_path).exists():
                    logger.info(f"Character {character.name} already has reference image: {character.reference_image_path}")
                    continue
                
                # Generate reference image for extracted characters only (those not in selected_character_names)
                try:
                    reference_image_path, seed = await generate_character_reference_image(
                        character=character,
                        job_id=job_id,
                        image_service=image_service
                    )
                    character.reference_image_path = reference_image_path
                    # Only set seed if not already set
                    if character.seed is None:
                        character.seed = seed
                    logger.info(f"Character reference image generated for extracted character {character.name}: {reference_image_path}, seed: {seed}")
                except Exception as e:
                    logger.warning(f"Failed to generate character reference image for {character.name}: {e}. Continuing without visual reference.")
                    if not character.reference_image_path:
                        character.reference_image_path = None
                    if character.seed is None:
                        character.seed = None
        else:
            logger.info("No characters to use")
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
        
        logger.info(f"Starting full-page image generation for {total_beats} beats")
        for i, beat in enumerate(base_storybook.beats, 1):
            if job_id in jobs:
                jobs[job_id].current_step = f"Generating full-page image for beat {i}/{total_beats}"
                progress = int(30 + (30 * (i - 1) / total_beats))
                jobs[job_id].progress = progress
            
            # Generate full-page scene image using background prompt
            background_prompt = all_background_prompts.get(i)
            logger.info(f"Beat {i}: background_prompt exists: {background_prompt is not None}")
            if background_prompt:
                logger.info(f"Beat {i}: Generating image with prompt (first 200 chars): {background_prompt.prompt[:200] if background_prompt.prompt else 'None'}...")
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
                    logger.info(f"Beat {i}: Calling image_service.generate_image...")
                    raw_image_data = await image_service.generate_image(
                        prompt=fullpage_prompt,
                        size="1024x1024"
                    )
                    logger.info(f"Beat {i}: Image service returned {len(raw_image_data) if raw_image_data else 0} bytes")
                    
                    if not raw_image_data:
                        raise ValueError(f"Image service returned empty image data for beat {i}")
                    
                    # Save full-page image
                    assets_dir = ensure_job_directory(job_id)
                    fullpage_filename = f"beat_{i}_fullpage.png"
                    fullpage_path = assets_dir / fullpage_filename
                    
                    logger.info(f"Beat {i}: Saving image to {fullpage_path}")
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
                    logger.error(f"Failed to generate full-page image for beat {i}: {e}", exc_info=True)
                    image_paths[i] = None
            else:
                logger.warning(f"No background prompt for beat {i}. Skipping image generation.")
                image_paths[i] = None
        
        logger.info(f"Image generation complete. Generated {len([p for p in image_paths.values() if p])} out of {total_beats} images.")
        
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
            # Pass stored characters to maintain consistency across languages
            storybook = await generate_storybook_content(
                theme=theme or "adventure",
                num_pages=num_pages,
                language=language,
                characters=stored_characters,  # Pass stored characters for consistency
                llm_client=llm_client
            )
            
            # Use the same images and cover for all languages
            storybook.cover_image_path = cover_image_path
            storybook.characters = base_storybook.characters  # Use same characters
            
            # Generate PDF for this language - run in thread pool to avoid blocking event loop
            # This allows status updates to continue while PDF generation happens
            logger.info(f"Starting PDF generation for language {language} (job {job_id})")
            try:
                # Create a partial function with all arguments to pass to thread executor
                pdf_gen_func = partial(
                    generate_pdf,
                    storybook=storybook,
                    job_id=job_id,
                    image_paths=image_paths,
                    cover_image_path=cover_image_path,
                    synopsis=storybook.synopsis,
                    language=language,
                    pod_ready=pod_ready
                )
                
                # Use asyncio.to_thread if available (Python 3.9+), otherwise use executor
                if hasattr(asyncio, 'to_thread'):
                    pdf_path = await asyncio.to_thread(pdf_gen_func)
                else:
                    # Fallback for Python < 3.9
                    loop = asyncio.get_event_loop()
                    pdf_path = await loop.run_in_executor(None, pdf_gen_func)
                
                logger.info(f"PDF generation completed for language {language}: {pdf_path}")
            except Exception as e:
                error_msg = f"Error generating PDF for language {language}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                # Update status to show partial failure
                if job_id in jobs:
                    jobs[job_id].current_step = f"PDF generation failed for {language}: {str(e)}"
                raise
            
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
    theme: Optional[str] = Query(None), 
    num_pages: int = Query(5), 
    style: Optional[str] = Query(None),
    languages: Optional[List[str]] = Query(None),
    pod_ready: bool = Query(False),
    character_ids: Optional[List[str]] = Query(None),
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
        character_ids: Optional list of character IDs to use from character storage
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
    
    # Validate character_ids if provided
    if character_ids:
        for char_id in character_ids:
            if not character_exists(char_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Character not found: {char_id}"
                )
    
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
    
    background_tasks.add_task(process_storybook_job, job_id, theme, num_pages, style, languages, pod_ready, character_ids)
    
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


@app.get("/characters")
async def list_all_characters():
    """
    List all characters in storage.
    
    Returns:
        List of character metadata
    """
    try:
        characters = list_characters()
        return {"characters": characters}
    except Exception as e:
        logger.error(f"Error listing characters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list characters: {str(e)}")


@app.get("/characters/{character_id}")
async def get_character_details(character_id: str):
    """
    Get character details by ID.
    
    Args:
        character_id: Character ID (with or without chr_ prefix)
        
    Returns:
        Character metadata
    """
    if not character_exists(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    
    try:
        data = load_character(character_id)
        if not data:
            raise HTTPException(status_code=404, detail="Character not found")
        return data
    except Exception as e:
        logger.error(f"Error loading character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load character: {str(e)}")


@app.post("/characters")
async def create_character(
    name: str = Form(...),
    species: Optional[str] = Form(None),
    physical_description: str = Form(...),
    key_features: Optional[str] = Form(None),  # JSON string or comma-separated
    color_palette: Optional[str] = Form(None),  # JSON string
    tags: Optional[str] = Form(None),  # JSON string or comma-separated
    generate_image: bool = Form(False),
    image: Optional[UploadFile] = File(None)
):
    """
    Create a new character.
    
    Args:
        name: Character name
        species: Optional species
        physical_description: Detailed physical description
        key_features: Comma-separated or JSON array string
        color_palette: JSON object string
        tags: Comma-separated or JSON array string
        generate_image: If True, generate image using AI
        image: Optional uploaded image file
        
    Returns:
        Created character metadata with character_id
    """
    try:
        # Parse key_features
        features_list = []
        if key_features:
            try:
                features_list = json.loads(key_features)
            except json.JSONDecodeError:
                features_list = [f.strip() for f in key_features.split(",") if f.strip()]
        
        # Parse color_palette
        palette_dict = None
        if color_palette:
            try:
                palette_dict = json.loads(color_palette)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid color_palette JSON")
        
        # Parse tags
        tags_list = []
        if tags:
            try:
                tags_list = json.loads(tags)
            except json.JSONDecodeError:
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Create Character object
        character = Character(
            name=name,
            species=species,
            physical_description=physical_description,
            key_features=features_list,
            color_palette=palette_dict
        )
        
        # Generate refined prompt
        character.refined_prompt = create_refined_character_prompt(character)
        
        # Handle image
        image_data = None
        if image:
            # Use uploaded image
            image_data = await image.read()
        elif generate_image:
            # Generate image using AI
            try:
                image_service = get_image_service()
                # Use a temporary job_id for image generation
                temp_job_id = str(uuid.uuid4())
                reference_image_path, seed = await generate_character_reference_image(
                    character=character,
                    job_id=temp_job_id,
                    image_service=image_service
                )
                character.seed = seed
                # Read the generated image
                with open(reference_image_path, 'rb') as f:
                    image_data = f.read()
            except Exception as e:
                logger.warning(f"Failed to generate character image: {e}")
        
        # Save character
        character_id = save_character(character, image_data, tags_list)
        
        # Return created character
        data = load_character(character_id)
        if data:
            data['character_id'] = character_id
            return data
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve created character")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create character: {str(e)}")


@app.put("/characters/{character_id}")
async def update_character(
    character_id: str,
    name: Optional[str] = Form(None),
    species: Optional[str] = Form(None),
    physical_description: Optional[str] = Form(None),
    key_features: Optional[str] = Form(None),
    color_palette: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Update an existing character.
    
    Args:
        character_id: Character ID to update
        name: Optional new name
        species: Optional new species
        physical_description: Optional new description
        key_features: Optional new features (JSON or comma-separated)
        color_palette: Optional new palette (JSON)
        tags: Optional new tags (JSON or comma-separated)
        image: Optional new image file
        
    Returns:
        Updated character metadata
    """
    if not character_exists(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    
    try:
        # Load existing character
        existing_data = load_character(character_id)
        if not existing_data:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Update fields if provided
        if name:
            existing_data['name'] = name
        if species is not None:
            existing_data['species'] = species
        if physical_description:
            existing_data['physical_description'] = physical_description
        if key_features is not None:
            try:
                existing_data['key_features'] = json.loads(key_features)
            except json.JSONDecodeError:
                existing_data['key_features'] = [f.strip() for f in key_features.split(",") if f.strip()]
        if color_palette is not None:
            try:
                existing_data['color_palette'] = json.loads(color_palette)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid color_palette JSON")
        if tags is not None:
            try:
                existing_data['tags'] = json.loads(tags)
            except json.JSONDecodeError:
                existing_data['tags'] = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Convert to Character object
        character = dict_to_character(existing_data)
        
        # Regenerate refined prompt if description changed
        if physical_description or key_features is not None or color_palette is not None:
            character.refined_prompt = create_refined_character_prompt(character)
            existing_data['refined_prompt'] = character.refined_prompt
        
        # Handle image update
        image_data = None
        if image:
            image_data = await image.read()
        
        # Save updated character
        save_character(character, image_data, existing_data.get('tags', []))
        
        # Return updated character
        updated_data = load_character(character_id)
        if updated_data:
            updated_data['character_id'] = character_id
            return updated_data
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated character")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update character: {str(e)}")


@app.delete("/characters/{character_id}")
async def delete_character_endpoint(character_id: str):
    """
    Delete a character.
    
    Args:
        character_id: Character ID to delete
        
    Returns:
        Success message
    """
    if not character_exists(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    
    try:
        deleted = delete_character(character_id)
        if deleted:
            return {"message": "Character deleted successfully", "character_id": character_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete character")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete character: {str(e)}")


@app.get("/characters/{character_id}/image")
async def get_character_image(character_id: str):
    """
    Get character image file.
    
    Args:
        character_id: Character ID
        
    Returns:
        Image file response
    """
    image_path = get_character_image_path(character_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="Character image not found")
    
    return FileResponse(
        str(image_path),
        media_type="image/png",
        filename=f"{character_id}_image.png"
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Story Booker API",
        "version": "0.3.1",
        "description": "AI Sticker-Book Generator"
    }
