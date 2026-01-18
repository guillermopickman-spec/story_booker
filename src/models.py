"""
Pydantic models for Story Booker application.
"""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel


class StoryBeat(BaseModel):
    """Represents a single story beat with text and visual elements."""
    text: str
    visual_description: str
    sticker_subjects: List[str]


class Character(BaseModel):
    """Represents a character with physical attributes for visual consistency."""
    name: str
    species: Optional[str] = None
    physical_description: str  # Detailed description
    key_features: List[str] = []  # Distinctive features
    color_palette: Optional[Dict[str, Optional[str]]] = None  # hair_color, eye_color, etc.
    reference_image_path: Optional[str] = None  # Path to reference/concept art image
    seed: Optional[int] = None  # Seed for image generation consistency (Pollinations/Flux)
    refined_prompt: Optional[str] = None  # Refined, detailed prompt for consistent image generation


class StoryBook(BaseModel):
    """Represents a complete storybook with title and beats."""
    title: str
    beats: List[StoryBeat]
    characters: List[Character] = []  # Main characters for consistency (can have multiple)
    synopsis: Optional[str] = None  # Brief story summary for back cover
    cover_image_path: Optional[str] = None  # Path to generated cover image
    author_bio: Optional[str] = None  # Brief author/creator biography for "About the Author" page


class JobStatus(BaseModel):
    """Represents the status of a storybook generation job."""
    job_id: str
    status: str
    file_path: Optional[str] = None  # Primary file path (for backward compatibility)
    file_paths: Optional[Dict[str, str]] = None  # Map of language to file path (e.g., {"en": "path/to/en.pdf", "es": "path/to/es.pdf"})
    progress: Optional[int] = None
    error_message: Optional[str] = None
    current_step: Optional[str] = None


class ImagePrompt(BaseModel):
    """Represents an image generation prompt for a sticker."""
    prompt: str
    subject: str


class CharacterMetadata(BaseModel):
    """Represents character metadata for storage, includes tags and timestamps."""
    name: str
    species: Optional[str] = None
    physical_description: str
    key_features: List[str] = []
    color_palette: Optional[Dict[str, Optional[str]]] = None
    tags: List[str] = []
    created_at: str
    updated_at: str
    seed: Optional[int] = None
    refined_prompt: Optional[str] = None
    character_id: Optional[str] = None  # Added when loading from storage
    has_image: Optional[bool] = None  # Added when loading from storage
