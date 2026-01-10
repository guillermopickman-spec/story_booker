"""
Tests for image generation service with mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.image_service import ImageService, ImageProvider


class TestImageService:
    """Tests for ImageService initialization and configuration."""
    
    def test_service_initialization_default(self):
        """Test service initializes with default provider (pollinations)."""
        with patch.dict('os.environ', {'IMAGE_PROVIDER': 'pollinations'}):
            service = ImageService()
            assert service.provider == "pollinations"
    
    def test_service_initialization_with_provider(self):
        """Test service can be initialized with specific provider."""
        service = ImageService(provider="openai")
        assert service.provider == "openai"
    
    def test_service_invalid_provider(self):
        """Test service raises error for invalid provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ImageService(provider="invalid_provider")


class TestImageGeneration:
    """Tests for image generation methods."""
    
    @pytest.mark.asyncio
    async def test_generate_mock_image(self):
        """Test mock image generation."""
        service = ImageService(provider="mock")
        
        image_data = await service.generate_image("test prompt", size="512x512")
        
        assert isinstance(image_data, bytes)
        assert len(image_data) > 0
        # Should be valid PNG
        assert image_data[:8] == b'\x89PNG\r\n\x1a\n'
    
    @pytest.mark.asyncio
    async def test_generate_pollinations_image(self):
        """Test Pollinations.ai image generation."""
        service = ImageService(provider="pollinations")
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTP response
            mock_response = AsyncMock()
            mock_response.content = b'\x89PNG\r\n\x1a\n' + b'fake_png_data'
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance
            
            image_data = await service.generate_image("test prompt", size="512x512")
            
            assert isinstance(image_data, bytes)
            assert len(image_data) > 0
            mock_client_instance.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_openai_image(self):
        """Test OpenAI DALL-E image generation."""
        service = ImageService(provider="openai")
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Mock the openai module import
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                      MagicMock(AsyncOpenAI=MagicMock(return_value=AsyncMock())) if name == 'openai' else __import__(name, *args, **kwargs)):
                # Mock the import inside the method
                with patch.object(service, '_generate_openai') as mock_method:
                    # Mock the response
                    mock_method.return_value = b'\x89PNG\r\n\x1a\n' + b'fake_png_data'
                    
                    image_data = await service.generate_image("test prompt", size="1024x1024")
                    
                    assert isinstance(image_data, bytes)
                    assert len(image_data) > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback(self):
        """Test automatic fallback when primary provider fails."""
        service = ImageService(provider="pollinations")
        
        # Mock pollinations to fail, mock to succeed
        with patch.object(service, '_generate_pollinations', side_effect=Exception("Pollinations error")):
            with patch.object(service, '_generate_openai', side_effect=Exception("OpenAI error")):
                # Mock provider should work
                image_data = await service.generate_image("test prompt", use_fallback=True)
                
                assert isinstance(image_data, bytes)
                assert len(image_data) > 0
    
    @pytest.mark.asyncio
    async def test_generate_no_fallback(self):
        """Test that fallback is not used when disabled."""
        service = ImageService(provider="pollinations")
        
        with patch.object(service, '_generate_pollinations', side_effect=Exception("Pollinations error")):
            with pytest.raises(Exception, match="Pollinations error"):
                await service.generate_image("test prompt", use_fallback=False)


class TestImageProviderEnum:
    """Tests for ImageProvider enum."""
    
    def test_provider_enum_values(self):
        """Test provider enum has correct values."""
        assert ImageProvider.POLLINATIONS.value == "pollinations"
        assert ImageProvider.OPENAI.value == "openai"
        assert ImageProvider.MOCK.value == "mock"
