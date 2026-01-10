"""
Pydantic models for Story Booker application.
"""

from typing import List, Optional
from pydantic import BaseModel


class StoryBeat(BaseModel):
    """Represents a single story beat with text and visual elements."""
    text: str
    visual_description: str
    sticker_subjects: List[str]


class StoryBook(BaseModel):
    """Represents a complete storybook with title and beats."""
    title: str
    beats: List[StoryBeat]


class JobStatus(BaseModel):
    """Represents the status of a storybook generation job."""
    job_id: str
    status: str
    file_path: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    current_step: Optional[str] = None


class ImagePrompt(BaseModel):
    """Represents an image generation prompt for a sticker."""
    prompt: str
    subject: str
