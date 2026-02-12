import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Story Booker Test API")

# Setup CORS so Next.js can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None

class ImageResponse(BaseModel):
    success: bool
    message: str
    image_data: Optional[str] = None
    prompt_id: Optional[str] = None

class DescriptionRequest(BaseModel):
    prompt: str
    character_name: Optional[str] = None
    aspects: Optional[list] = None
    style: Optional[str] = None

class DescriptionResponse(BaseModel):
    success: bool
    message: str
    description: Optional[str] = None
    modular_description: Optional[dict] = None
    formatted_prompts: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "Story Booker Backend is Live", "status": "online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/generate-image")
async def generate_image(request: ImageRequest):
    """
    Generate an image using the configured ComfyUI workflow.
    """
    try:
        # For testing, return a placeholder image
        placeholder_image = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Crect width='400' height='400' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' font-size='20' text-anchor='middle' fill='%23666'%3EGenerated Image%3C/text%3E%3C/svg%3E"
        
        return ImageResponse(
            success=True,
            message="Image generated successfully (test mode)",
            image_data=placeholder_image,
            prompt_id="test-prompt-id"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-description")
async def generate_description(request: DescriptionRequest):
    """
    Generate a character description using Ollama.
    """
    try:
        # For testing, return a placeholder description
        test_description = f"A character named {request.character_name or 'Unknown'} with {request.style or 'storybook'} style."
        
        response_data = {
            "success": True,
            "message": "Description generated successfully (test mode)",
            "description": test_description,
            "modular_description": {
                "appearance": test_description,
                "personality": "Brave and adventurous",
                "background": "From a mystical realm"
            },
            "formatted_prompts": {
                "positive": test_description,
                "negative": "blurry, low quality"
            }
        }
        
        return DescriptionResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image-with-description")
async def generate_image_with_description(request: DescriptionRequest):
    """
    Generate a character description and then create an image using ComfyUI.
    """
    try:
        # Generate description (test)
        test_description = f"A character named {request.character_name or 'Unknown'} with {request.style or 'storybook'} style."
        
        # Return placeholder image
        placeholder_image = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Crect width='400' height='400' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' font-size='20' text-anchor='middle' fill='%23666'%3ECharacter Image%3C/text%3E%3C/svg%3E"
        
        return ImageResponse(
            success=True,
            message="Description and image generated successfully (test mode)",
            image_data=placeholder_image,
            prompt_id="test-prompt-id"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)