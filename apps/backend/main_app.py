'''
API endpoints for Story Booker - Backend service for character image generation
'''

import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our actual image generation function
from apps.backend.main import get_generated_image

# Import image generation manager
from modules.characters.image_gen.manager import ImageGenManager

app = FastAPI(title='Story Booker API')

# Setup CORS so frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:3001'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None

class ImageResponse(BaseModel):
    success: bool
    message: str
    image_data: Optional[str] = None
    prompt_id: Optional[str] = None

class GenerateImageWithDescriptionRequest(BaseModel):
    character_name: Optional[str] = None
    prompt: Optional[str] = None
    style: str

class GenerateImageWithDescriptionResponse(BaseModel):
    success: bool
    message: str
    prompt_id: Optional[str] = None
    status: str  # 'queued' or 'generating'

@app.get('/')
async def root():
    return {'message': 'Story Booker Backend is Live', 'status': 'online'}

@app.get('/health')
async def health_check():
    return {'status': 'healthy'}

@app.post('/generate-image')
async def generate_image(request: ImageRequest):
    '''
    Generate an image using ComfyUI and return the prompt ID.
    The frontend should poll /image/{prompt_id} to get the result.
    '''
    try:
        # Initialize image generator
        image_manager = ImageGenManager()

        # Check if ComfyUI is accessible
        if not image_manager.check_comfyui_connection():
            raise HTTPException(
                status_code=503,
                detail='ComfyUI is not accessible. Please make sure ComfyUI is running.'
            )

        # Generate the image
        result = image_manager.generate_image(
            user_pos=request.prompt,
            user_neg=request.negative_prompt
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail='Failed to generate image. Please try again.'
            )

        prompt_id = result.get('prompt_id')
        if not prompt_id:
            raise HTTPException(
                status_code=500,
                detail='Image generation started but no prompt ID returned.'
            )

        return ImageResponse(
            success=True,
            message='Image generation started successfully',
            prompt_id=prompt_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-image-with-description')
async def generate_image_with_description(request: GenerateImageWithDescriptionRequest):
    '''
    Generate an image using ComfyUI and return the prompt ID.
    The frontend should poll /image/{prompt_id} to get the result.
    '''
    try:
        # Initialize image generator
        image_manager = ImageGenManager()

        # Check if ComfyUI is accessible
        if not image_manager.check_comfyui_connection():
            raise HTTPException(
                status_code=503,
                detail='ComfyUI is not accessible. Please make sure ComfyUI is running.'
            )

        # Construct the full prompt from character name, user prompt, and style
        base_prompt = ''
        if request.character_name:
            base_prompt += f'Character name: {request.character_name}. '
        if request.prompt:
            base_prompt += request.prompt

        # Add style to the prompt
        style_suffixes = {
            'storybook': 'storybook style, fantasy art, detailed illustrations',
            'anime': 'anime style, vibrant colors, expressive eyes',
            'pixar': 'Pixar-style 3D animation, colorful, clean',
            'ghibli': 'Studio Ghibli style, hand-drawn, dreamy',
            'cyberpunk': 'cyberpunk aesthetic, neon lights, futuristic',
            'disney_90s': 'Disney 90s style, classic animated, vibrant',
            'arcane': 'Arcane/League of Legends style, fantasy cityscape',
            'vaporwave': 'vaporwave aesthetic, 80s inspired, soft colors',
            'retro_anime': 'retro anime style, 90s inspired, dramatic lighting',
            'overwatch': 'Overwatch game style, clean digital art',
            'spiderverse': 'Spider-Verse style, comic book aesthetic, dynamic'
        }

        full_prompt = base_prompt
        if request.style and request.style in style_suffixes:
            full_prompt += f', {style_suffixes[request.style]}'
        else:
            full_prompt += ', default style'

        # Generate the image
        result = image_manager.generate_image(user_pos=full_prompt)

        if not result:
            raise HTTPException(
                status_code=500,
                detail='Failed to start image generation.'
            )

        prompt_id = result.get('prompt_id')
        if not prompt_id:
            raise HTTPException(
                status_code=500,
                detail='Image generation started but no prompt ID was returned.'
            )

        return GenerateImageWithDescriptionResponse(
            success=True,
            message='Image generation queued successfully',
            prompt_id=prompt_id,
            status='queued'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/image/{prompt_id}')
async def get_image(prompt_id: str):
    '''
    Retrieve a generated image by prompt ID.
    '''
    try:
        base64_image = await get_generated_image(prompt_id)

        if base64_image:
            return {
                'success': True,
                'message': 'Image retrieved successfully',
                'image_data': base64_image
            }
        else:
            raise HTTPException(status_code=404, detail='Image not found or generation failed')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
