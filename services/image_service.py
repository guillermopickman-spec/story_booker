"""
Image Generation Service: Unified interface for multiple image generation providers.
Supports Pollinations.ai (authenticated only), OpenAI DALL-E, and mock provider for testing.

Pollinations API Key:
    - REQUIRED: Set POLLINATIONS_API_KEY environment variable for authenticated access
    - Uses enter.pollinations.ai authenticated API endpoint only
    - Free tier is no longer supported - API key is mandatory
"""

import os
import asyncio
import logging
from enum import Enum
from typing import Optional
from io import BytesIO
import httpx
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

logger = logging.getLogger(__name__)


class ImageProvider(str, Enum):
    """Supported image generation providers."""
    POLLINATIONS = "pollinations"
    OPENAI = "openai"
    MOCK = "mock"


class ImageService:
    """Unified image generation service that can switch between different providers."""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize image service with specified provider.
        
        Args:
            provider: The image provider to use (pollinations, openai, mock). Defaults to pollinations.
        """
        provider_str = provider or os.getenv("IMAGE_PROVIDER", "pollinations")
        provider_str = provider_str.lower()
        
        if provider_str not in [p.value for p in ImageProvider]:
            raise ValueError(f"Unknown provider: {provider_str}. Must be one of: {[p.value for p in ImageProvider]}")
        
        self.provider = provider_str
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        use_fallback: bool = True
    ) -> bytes:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (e.g., "1024x1024", "512x512")
            use_fallback: If True, try fallback providers on failure
            
        Returns:
            Image bytes (PNG format)
            
        Raises:
            asyncio.TimeoutError: If the operation exceeds the configured timeout
        """
        timeout_seconds = float(os.getenv("IMAGE_TIMEOUT", "180"))
        providers_to_try = [self.provider]
        
        if use_fallback:
            fallback_order = {
                "pollinations": ["openai", "mock"],
                "openai": ["pollinations", "mock"],
                "mock": ["pollinations", "openai"]
            }
            providers_to_try.extend(fallback_order.get(self.provider, []))
        
        last_error = None
        for provider in providers_to_try:
            try:
                if provider == "pollinations":
                    result = await asyncio.wait_for(
                        self._generate_pollinations(prompt, size),
                        timeout=timeout_seconds
                    )
                    return result
                elif provider == "openai":
                    result = await asyncio.wait_for(
                        self._generate_openai(prompt, size),
                        timeout=timeout_seconds
                    )
                    return result
                elif provider == "mock":
                    result = await asyncio.wait_for(
                        self._generate_mock(prompt, size),
                        timeout=timeout_seconds
                    )
                    return result
            except asyncio.TimeoutError:
                timeout_msg = f"Image generation timed out after {timeout_seconds}s using provider '{provider}'"
                last_error = TimeoutError(timeout_msg)
                if provider == providers_to_try[-1]:
                    raise last_error
                continue
            except Exception as e:
                last_error = e
                if provider == providers_to_try[-1]:
                    raise
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def _is_rate_limit_error(self, response: Optional[httpx.Response], error: Exception) -> bool:
        """
        Check if error is a rate limit/API limit error.
        
        Args:
            response: HTTP response object (if available)
            error: Exception that was raised
            
        Returns:
            True if the error indicates a rate limit, False otherwise
        """
        if response and response.status_code == 429:
            return True
        
        error_str = str(error).lower()
        limit_keywords = ["limited", "rate limit", "quota", "limit exceeded", "too many requests", "api is limited"]
        if any(keyword in error_str for keyword in limit_keywords):
            return True
        
        if response:
            try:
                response_text = response.text.lower()
                if any(keyword in response_text for keyword in limit_keywords):
                    return True
            except:
                pass
        
        return False
    
    def _is_valid_pollinations_api_key(self, api_key: Optional[str]) -> bool:
        """
        Check if Pollinations API key is valid (not placeholder or empty).
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if the key is valid, False otherwise
        """
        if not api_key or not api_key.strip():
            return False
        
        placeholder_values = [
            "your_pollinations_api_key_here",
            "your_api_key_here",
            ""
        ]
        
        return api_key.strip().lower() not in [p.lower() for p in placeholder_values]
    
    async def _generate_pollinations(self, prompt: str, size: str) -> bytes:
        """
        Generate image using Pollinations.ai authenticated API.
        
        Uses enter.pollinations.ai authenticated endpoint only.
        API key is REQUIRED - free tier is no longer supported.
        
        API Documentation: https://enter.pollinations.ai/api/docs
        
        Args:
            prompt: Image generation prompt
            size: Image size (widthxheight)
            
        Returns:
            Image bytes
            
        Raises:
            ValueError: If API key is missing or invalid
            RuntimeError: If API request fails
        """
        from urllib.parse import quote
        
        api_key = os.getenv("POLLINATIONS_API_KEY")
        has_valid_key = self._is_valid_pollinations_api_key(api_key)
        
        if not has_valid_key:
            raise ValueError(
                "POLLINATIONS_API_KEY is required. "
                "Free tier is no longer supported. "
                "Please set a valid API key in your .env file. "
                "Get your API key at: https://enter.pollinations.ai"
            )
        
        width, height = map(int, size.split('x'))
        
        # Use authenticated enter.pollinations.ai endpoint
        encoded_prompt = quote(prompt)
        url = f"https://enter.pollinations.ai/api/generate/image/{encoded_prompt}"
        
        params = {
            "model": "flux",
            "width": width,
            "height": height
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Using Pollinations.ai authenticated API (enter.pollinations.ai) with model=flux, size={width}x{height}")
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                if "image" not in content_type.lower():
                    response_text = response.text.lower()
                    limit_keywords = ["limited", "rate limit", "quota", "limit exceeded", "too many requests", "api is limited"]
                    is_rate_limit_in_text = any(keyword in response_text for keyword in limit_keywords)
                    
                    if is_rate_limit_in_text:
                        logger.error(f"Pollinations.ai rate limit reached. Response: {response.text[:200]}")
                        raise RuntimeError(
                            f"Pollinations.ai rate limit reached with authenticated API key. "
                            f"This indicates the API key quota has been exceeded. Response: {response.text[:200]}"
                        )
                    else:
                        raise ValueError(
                            f"Unexpected content type from Pollinations.ai: {content_type}. "
                            f"Expected image, got: {content_type}. Response: {response.text[:200]}"
                        )
                
                logger.debug("Successfully generated image from Pollinations.ai authenticated API")
                return response.content
                
            except httpx.HTTPStatusError as e:
                response = e.response
                status_code = response.status_code if response else None
                
                if status_code == 401:
                    logger.error("Pollinations.ai authentication failed - invalid API key")
                    raise ValueError(
                        "Pollinations.ai authentication failed. "
                        "Please check that your POLLINATIONS_API_KEY is valid. "
                        f"Status: {status_code}, Response: {response.text[:200] if response else 'No response'}"
                    ) from e
                elif status_code == 429:
                    logger.error("Pollinations.ai rate limit exceeded")
                    raise RuntimeError(
                        f"Pollinations.ai rate limit exceeded. "
                        f"Your API key quota has been reached. Status: {status_code}"
                    ) from e
                else:
                    is_rate_limit = self._is_rate_limit_error(response, e)
                    if is_rate_limit:
                        logger.error(f"Pollinations.ai rate limit error: {e}")
                        raise RuntimeError(
                            f"Pollinations.ai rate limit reached with authenticated API key. "
                            f"This indicates the API key quota has been exceeded. Status: {status_code}, Error: {e}"
                        ) from e
                    else:
                        logger.error(f"Pollinations.ai API error: {e}")
                        raise RuntimeError(
                            f"Failed to generate image from Pollinations.ai authenticated API. "
                            f"Status: {status_code}, Error: {e}"
                        ) from e
            except httpx.HTTPError as e:
                logger.error(f"Pollinations.ai HTTP error: {e}")
                raise RuntimeError(f"Failed to generate image from Pollinations.ai: {e}") from e
    
    async def _generate_openai(self, prompt: str, size: str) -> bytes:
        """
        Generate image using OpenAI DALL-E.
        
        Args:
            prompt: Image generation prompt
            size: Image size (must be one of OpenAI's supported sizes)
            
        Returns:
            Image bytes
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        client = AsyncOpenAI(api_key=api_key        )
        
        size_map = {
            "1024x1024": "1024x1024",
            "512x512": "512x512",
            "256x256": "256x256"
        }
        dall_e_size = size_map.get(size, "1024x1024")
        
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            # Fix: Make sure size is one of the supported literals for DALL-E
            size=dall_e_size if dall_e_size in ("1024x1024", "512x512", "256x256") else "1024x1024",
            quality="standard",
            n=1,
            response_format="url"
        )
        
        if not response.data or not response.data[0].url:
            raise ValueError("No image URL returned from OpenAI")
        
        image_url = response.data[0].url
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            img_response = await http_client.get(image_url)
            img_response.raise_for_status()
            return img_response.content
    
    async def _generate_mock(self, prompt: str, size: str) -> bytes:
        """
        Generate a mock placeholder image for testing.
        
        Args:
            prompt: Image generation prompt (not used, but kept for interface consistency)
            size: Image size
            
        Returns:
            Mock image bytes
        """
        width, height = map(int, size.split('x'))
        
        image = Image.new('RGB', (width, height), color=(240, 240, 255))
        
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 10, width-10, height-10], outline=(100, 150, 200), width=5)
        
        text = prompt[:50] + "..." if len(prompt) > 50 else prompt
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=(50, 50, 50), font=font)
        
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()


def get_image_service(provider: Optional[str] = None) -> ImageService:
    """Get an image service instance."""
    return ImageService(provider=provider)
