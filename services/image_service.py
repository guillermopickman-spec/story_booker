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
from typing import Optional, List
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
        seed: Optional[int] = None,
        character_description: Optional[str] = None,
        use_fallback: bool = True
    ) -> bytes:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (e.g., "1024x1024", "512x512")
            seed: Optional seed for consistency (Pollinations/Flux)
            character_description: Optional character description for DALL-E consistency
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
                "pollinations": ["openai", "mock"],  # Fallback to openai, then mock as last resort
                "openai": ["pollinations", "mock"],  # Fallback to pollinations, then mock as last resort
                "mock": ["pollinations", "openai"]  # Mock can fallback to real providers
            }
            providers_to_try.extend(fallback_order.get(self.provider, []))
        
        last_error = None
        logger.info(f"Image generation: trying provider '{self.provider}' first (with fallback: {use_fallback})")
        for provider in providers_to_try:
            try:
                logger.info(f"Attempting image generation with provider: {provider}")
                if provider == "pollinations":
                    result = await asyncio.wait_for(
                        self._generate_pollinations(prompt, size, seed),
                        timeout=timeout_seconds
                    )
                    logger.info(f"Successfully generated image using provider: {provider}, size: {len(result) if result else 0} bytes")
                    return result
                elif provider == "openai":
                    result = await asyncio.wait_for(
                        self._generate_openai(prompt, size, character_description),
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
                logger.warning(f"Image generation timed out with provider '{provider}': {timeout_msg}")
                last_error = TimeoutError(timeout_msg)
                if provider == providers_to_try[-1]:
                    raise last_error
                logger.info(f"Trying fallback provider...")
                continue
            except Exception as e:
                logger.warning(f"Image generation failed with provider '{provider}': {type(e).__name__}: {str(e)}")
                last_error = e
                if provider == providers_to_try[-1]:
                    logger.error(f"All image providers failed. Last error: {last_error}")
                    raise
                logger.info(f"Trying fallback provider...")
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def _is_rate_limit_error(self, response: Optional[httpx.Response], error: Exception) -> bool:
        """
        Check if an error is related to rate limiting.
        
        Args:
            response: HTTP response object (if available)
            error: Exception that was raised
            
        Returns:
            True if error is rate limit related, False otherwise
        """
        error_str = str(error).lower()
        limit_keywords = ["rate limit", "429", "too many requests", "quota", "limit exceeded", "api is limited"]
        
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
    
    async def _generate_pollinations(self, prompt: str, size: str, seed: Optional[int] = None, models: Optional[List[str]] = None) -> bytes:
        """
        Generate image using Pollinations.ai authenticated API.
        
        Uses gen.pollinations.ai/image/ endpoint with Bearer token authentication.
        API key is REQUIRED - free tier is no longer supported.
        
        API Documentation: https://enter.pollinations.ai/api/docs
        Endpoint format: https://gen.pollinations.ai/image/{prompt}?model={model}
        
        Args:
            prompt: Image generation prompt
            size: Image size (widthxheight)
            seed: Optional seed for consistency (same seed + same prompt = same image)
            models: Optional list of models to try in sequence. Defaults to common models.
            
        Returns:
            Image bytes
            
        Raises:
            ValueError: If API key is missing or invalid
            RuntimeError: If all model attempts fail
        """
        from urllib.parse import quote, urlencode
        
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
        
        # Default models to try in sequence if not provided
        if models is None:
            models = ["flux", "flux-pro", "flux-dev", "stable-diffusion-xl", "stable-diffusion-2.1", "stable-diffusion-1.5"]
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        seed_info = f", seed={seed}" if seed is not None else ""
        logger.info(f"Calling Pollinations.ai authenticated API (gen.pollinations.ai) with models: {models}, size={width}x{height}{seed_info}")
        logger.info(f"API key present: {bool(api_key)}, key length: {len(api_key) if api_key else 0}")
        
        # Try each model in sequence
        last_error = None
        for model_idx, model in enumerate(models):
            try:
                # Build URL with all query params in the string (matching example script format)
                encoded_prompt = quote(prompt)
                query_params = {"model": model}
                if width and height:
                    query_params["width"] = str(width)
                    query_params["height"] = str(height)
                if seed is not None:
                    query_params["seed"] = str(seed)
                
                query_string = urlencode(query_params)
                url = f"https://gen.pollinations.ai/image/{encoded_prompt}?{query_string}"
                
                logger.info(f"Trying Pollinations.ai with model '{model}' (attempt {model_idx + 1}/{len(models)})")
                logger.debug(f"Pollinations API URL: {url[:150]}...")  # Truncate long URLs
        
                # Retry logic for server errors (500, 502, 503, 504) - per model
                max_retries = 3
                retry_delay = 2.0  # seconds
                
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                    model_last_response = None
                    for attempt in range(1, max_retries + 1):
                        try:
                            if attempt > 1:
                                logger.info(f"Retry attempt {attempt}/{max_retries} for model '{model}'...")
                                await asyncio.sleep(retry_delay * (attempt - 1))  # Exponential backoff
                            
                            # Use stream=True to match the working example's behavior with requests.get(stream=True)
                            # Note: No params dict - all params are in the URL string
                            async with client.stream("GET", url, headers=headers) as response:
                                model_last_response = response
                                status_code = response.status_code
                                
                                # If 500-504 server error, retry (read response before continuing)
                                if 500 <= status_code <= 504 and attempt < max_retries:
                                    try:
                                        response_text = (await response.aread()).decode('utf-8', errors='ignore')[:500]
                                    except Exception:
                                        response_text = ""
                                    logger.warning(f"Pollinations.ai server error {status_code} on attempt {attempt}. Will retry...")
                                    continue
                                
                                # Check for non-success status codes and read error response
                                if status_code >= 400:
                                    response_text = ""
                                    try:
                                        response_text = (await response.aread()).decode('utf-8', errors='ignore')[:500]
                                    except Exception:
                                        pass
                                    
                                    # Handle 404 - model not found, try next model
                                    if status_code == 404:
                                        logger.warning(f"Pollinations.ai model '{model}' not found (404). Trying next model...")
                                        raise RuntimeError(f"Model '{model}' not found (404) - will try next model")
                                    
                                    if status_code == 401:
                                        logger.error("Pollinations.ai authentication failed - invalid API key")
                                        raise ValueError(
                                            "Pollinations.ai authentication failed (401 Unauthorized). "
                                            "Please check that your POLLINATIONS_API_KEY is valid and not expired. "
                                            f"Response: {response_text}"
                                        )
                                    elif status_code == 429:
                                        logger.error("Pollinations.ai rate limit exceeded")
                                        raise RuntimeError(
                                            f"Pollinations.ai rate limit exceeded (429). "
                                            f"Your API key quota has been reached. Response: {response_text}"
                                        )
                                    else:
                                        # For other 4xx errors, try next model (might be model-specific issue)
                                        logger.warning(f"Pollinations.ai API error {status_code} with model '{model}'. Response: {response_text[:200]}")
                                        raise RuntimeError(f"Model '{model}' failed with status {status_code} - will try next model")
                                
                                # Check content type
                                content_type = response.headers.get("content-type", "")
                                if "image" not in content_type.lower():
                                    # Read response text for error messages
                                    response_text = (await response.aread()).decode('utf-8', errors='ignore').lower()
                                    limit_keywords = ["limited", "rate limit", "quota", "limit exceeded", "too many requests", "api is limited"]
                                    is_rate_limit_in_text = any(keyword in response_text for keyword in limit_keywords)
                                    
                                    if is_rate_limit_in_text:
                                        logger.error(f"Pollinations.ai rate limit reached. Response: {response_text[:200]}")
                                        raise RuntimeError(
                                            f"Pollinations.ai rate limit reached with authenticated API key. "
                                            f"This indicates the API key quota has been exceeded. Response: {response_text[:200]}"
                                        )
                                    else:
                                        raise ValueError(
                                            f"Unexpected content type from Pollinations.ai: {content_type}. "
                                            f"Expected image, got: {content_type}. Response: {response_text[:200]}"
                                        )
                                
                                # Stream the response content in chunks (matching working example's iter_content)
                                image_bytes = bytearray()
                                async for chunk in response.aiter_bytes(chunk_size=8192):
                                    image_bytes.extend(chunk)
                                
                                logger.info(f"Successfully generated image using Pollinations.ai model '{model}'")
                                logger.debug(f"Image size: {len(image_bytes)} bytes")
                                return bytes(image_bytes)
                    
                        except httpx.HTTPStatusError as e:
                            response = e.response
                            status_code = response.status_code if response else None
                            # Read response text safely (may be streamed)
                            try:
                                if response:
                                    response_text = (await response.aread()).decode('utf-8', errors='ignore')[:500]
                                else:
                                    response_text = "No response body"
                            except Exception:
                                response_text = "Could not read response body"
                            
                            # Non-recoverable errors - don't try other models
                            if status_code == 401:
                                logger.error("Pollinations.ai authentication failed - invalid API key")
                                raise ValueError(
                                    "Pollinations.ai authentication failed (401 Unauthorized). "
                                    "Please check that your POLLINATIONS_API_KEY is valid and not expired. "
                                    f"Response: {response_text}"
                                ) from e
                            elif status_code == 429:
                                logger.error("Pollinations.ai rate limit exceeded")
                                raise RuntimeError(
                                    f"Pollinations.ai rate limit exceeded (429). "
                                    f"Your API key quota has been reached. Response: {response_text}"
                                ) from e
                            
                            # Retry server errors (500-504) for same model
                            if status_code is not None and 500 <= status_code <= 504 and attempt < max_retries:
                                logger.warning(f"Pollinations.ai server error ({status_code}) on attempt {attempt}. Will retry...")
                                continue
                            
                            # For 404 and other errors, break to try next model
                            logger.warning(f"Pollinations.ai HTTP error with model '{model}': Status {status_code}, Response: {response_text[:200]}")
                            raise RuntimeError(f"Model '{model}' failed with status {status_code}")
                            
                        except httpx.RequestError as e:
                            logger.error(f"Pollinations.ai request failed (network/connection error) with model '{model}': {type(e).__name__}: {e}")
                            if attempt < max_retries:
                                logger.warning(f"Network error on attempt {attempt}. Will retry...")
                                continue
                            # Network errors are not model-specific, break to try next model
                            raise RuntimeError(f"Network error with model '{model}'")
                        
                        except RuntimeError as e:
                            # Re-raise RuntimeErrors that are for model fallback
                            error_msg = str(e)
                            if "will try next model" in error_msg.lower() or "failed with status" in error_msg.lower() or "network error" in error_msg.lower():
                                raise  # Let it bubble up to model loop
                            raise  # Re-raise other RuntimeErrors
                        
                        except Exception as e:
                            # For other unexpected errors, try next model
                            logger.warning(f"Unexpected error with model '{model}': {type(e).__name__}: {str(e)}")
                            raise RuntimeError(f"Unexpected error with model '{model}': {str(e)}")
                    
                    # If we get here, all retries failed for this model
                    logger.warning(f"All retry attempts failed for model '{model}'. Trying next model...")
                    
            except RuntimeError as e:
                # Check if this is a recoverable error (model-specific) that should trigger next model
                error_msg = str(e).lower()
                if "will try next model" in error_msg or "failed with status" in error_msg or "network error" in error_msg or "unexpected error" in error_msg:
                    last_error = e
                    if model_idx < len(models) - 1:
                        logger.info(f"Model '{model}' failed, trying next model...")
                        continue
                    # If this was the last model, the error will be raised below
                    last_error = e
                else:
                    # Non-recoverable error, re-raise
                    raise
            except (ValueError, RuntimeError) as e:
                # These are non-recoverable (401, 429, etc.) - don't try other models
                raise
            except Exception as e:
                # Other exceptions - log and try next model if available
                last_error = e
                logger.warning(f"Error with model '{model}': {type(e).__name__}: {str(e)}")
                if model_idx < len(models) - 1:
                    logger.info(f"Trying next model...")
                    continue
        
        # If we get here, all models failed
        raise RuntimeError(
            f"All Pollinations.ai models failed. Tried: {models}. "
            f"Last error: {type(last_error).__name__}: {str(last_error) if last_error else 'Unknown error'}"
        )
    
    async def _generate_openai(self, prompt: str, size: str, character_description: Optional[str] = None) -> bytes:
        """
        Generate image using OpenAI DALL-E API.
        
        Args:
            prompt: Image generation prompt
            size: Image size (widthxheight, e.g., "1024x1024", "512x512")
            character_description: Optional character description for consistency
            
        Returns:
            Image bytes
            
        Raises:
            ValueError: If API key is missing or invalid
            RuntimeError: If API request fails
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "OpenAI library not installed. Install it with: pip install openai"
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI DALL-E. "
                "Please set it in your .env file."
            )
        
        # Validate API key is not a placeholder
        placeholder_values = ["your_openai_api_key_here", "your_api_key_here", ""]
        if api_key.strip().lower() in [p.lower() for p in placeholder_values]:
            raise ValueError(
                "OPENAI_API_KEY appears to be a placeholder value. "
                "Please set a valid API key in your .env file."
            )
        
        # Parse size
        width, height = map(int, size.split('x'))
        
        # DALL-E 3 supports specific sizes - map to supported literal types
        size_key = f"{width}x{height}"
        dall_e_size: str
        if size_key in ("1024x1024", "1792x1024", "1024x1792"):
            dall_e_size = size_key
        elif size_key in ("512x512", "256x256"):
            dall_e_size = size_key
        else:
            # Default to 1024x1024 if size not supported
            logger.warning(f"DALL-E size {size_key} not supported, using 1024x1024")
            dall_e_size = "1024x1024"
        
        # Type cast to satisfy type checker (DALL-E accepts these specific literals)
        from typing import cast, Literal
        dall_e_size_literal = cast(Literal["1024x1024", "1792x1024", "1024x1792", "512x512", "256x256"], dall_e_size)
        
        # Enhance prompt with character description if provided
        enhanced_prompt = prompt
        if character_description:
            enhanced_prompt = f"{character_description}. {prompt}"
        
        client = AsyncOpenAI(api_key=api_key)
        
        logger.info(f"Calling OpenAI DALL-E API with size={dall_e_size}")
        logger.debug(f"DALL-E prompt: {enhanced_prompt[:100]}...")
        
        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt[:4000],  # DALL-E 3 has 4000 char limit
                size=dall_e_size_literal,
                quality="standard",
                n=1
            )
            
            if not response.data or len(response.data) == 0:
                raise RuntimeError("OpenAI DALL-E returned no image data")
            
            image_url = response.data[0].url
            if not image_url:
                raise RuntimeError("OpenAI DALL-E returned image with no URL")
            
            # Download the image
            async with httpx.AsyncClient(timeout=60.0) as http_client:
                image_response = await http_client.get(image_url)
                image_response.raise_for_status()
                
                logger.debug("Successfully generated image from OpenAI DALL-E")
                return image_response.content
                
        except Exception as e:
            logger.error(f"OpenAI DALL-E API error: {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Failed to generate image from OpenAI DALL-E. "
                f"Error: {type(e).__name__}: {str(e)}"
            ) from e
    
    async def _generate_mock(self, prompt: str, size: str) -> bytes:
        """
        Generate a mock image for testing (returns a simple colored image).
        
        Args:
            prompt: Image generation prompt (ignored for mock)
            size: Image size (widthxheight)
            
        Returns:
            Image bytes (PNG format)
        """
        width, height = map(int, size.split('x'))
        
        # Create a simple colored image
        # Use a hash of the prompt to generate consistent colors
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        # Generate RGB values from hash
        r = int(prompt_hash[0:2], 16)
        g = int(prompt_hash[2:4], 16)
        b = int(prompt_hash[4:6], 16)
        
        # Create a simple gradient image
        image = Image.new('RGB', (width, height), color=(r, g, b))
        
        # Add some text to indicate it's a mock
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            text = "MOCK IMAGE"
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Get text size and center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            
            # Draw white text with black outline for visibility
            draw.text(position, text, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        except Exception:
            # If text drawing fails, just return the colored image
            pass
        
        # Convert to bytes
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        logger.debug(f"Generated mock image: {width}x{height}, color RGB({r}, {g}, {b})")
        return img_bytes.getvalue()


def get_image_service(provider: Optional[str] = None) -> ImageService:
    """
    Get an ImageService instance.
    
    Args:
        provider: Optional provider name (pollinations, openai, mock). 
                  Defaults to IMAGE_PROVIDER env var or "pollinations".
    
    Returns:
        ImageService instance
    """
    return ImageService(provider=provider)
