"""
Tests for LLM Client with provider switching and fallback.
Uses mocking to avoid actual API calls.
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from services.llm_client import LLMClient, LLMProvider, get_llm_client


class TestLLMClient:
    """Test LLM client initialization and configuration."""
    
    def test_client_initialization_default(self):
        """Test client initializes with default provider (groq)."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "groq"}):
            client = LLMClient()
            assert client.provider == "groq"
            assert client.model is not None
    
    def test_client_initialization_with_provider(self):
        """Test client can be initialized with specific provider."""
        client = LLMClient(provider="openai")
        assert client.provider == "openai"
    
    def test_client_initialization_with_model(self):
        """Test client can be initialized with specific model."""
        client = LLMClient(provider="groq", model="custom-model")
        assert client.model == "custom-model"
    
    def test_client_invalid_provider(self):
        """Test client raises error for invalid provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMClient(provider="invalid_provider")
    
    def test_get_default_model_groq(self):
        """Test default model for Groq provider."""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(provider="groq")
            assert "llama" in client.model.lower() or client.model == os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    def test_get_default_model_openai(self):
        """Test default model for OpenAI provider."""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(provider="openai")
            assert "gpt" in client.model.lower() or client.model == os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def test_get_default_model_gpt4all(self):
        """Test default model for GPT4All provider."""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(provider="gpt4all")
            assert "Nous-Hermes" in client.model or client.model == os.getenv("GPT4ALL_MODEL_NAME", "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf")


class TestLLMClientGenerate:
    """Test LLM client generation methods."""
    
    @pytest.mark.asyncio
    async def test_generate_groq_success(self):
        """Test successful generation with Groq."""
        client = LLMClient(provider="groq", model="test-model")
        
        # Mock Groq client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        with patch.object(client, '_get_groq_client') as mock_get_client:
            mock_groq_client = AsyncMock()
            mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_groq_client
            
            result = await client.generate(
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7
            )
            
            assert result == "Test response"
            mock_groq_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_openai_success(self):
        """Test successful generation with OpenAI."""
        client = LLMClient(provider="openai", model="test-model")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI response"
        
        with patch.object(client, '_get_openai_client') as mock_get_client:
            mock_openai_client = AsyncMock()
            mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_openai_client
            
            result = await client.generate(
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7
            )
            
            assert result == "OpenAI response"
    
    @pytest.mark.asyncio
    async def test_generate_with_json_format(self):
        """Test generation with JSON response format."""
        client = LLMClient(provider="groq", model="test-model")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        
        with patch.object(client, '_get_groq_client') as mock_get_client:
            mock_groq_client = AsyncMock()
            mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_groq_client
            
            result = await client.generate(
                messages=[{"role": "user", "content": "Test"}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            assert result == '{"key": "value"}'
            # Verify JSON format was passed
            call_args = mock_groq_client.chat.completions.create.call_args
            assert "response_format" in call_args.kwargs
            assert call_args.kwargs["response_format"]["type"] == "json_object"
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback(self):
        """Test automatic fallback when primary provider fails."""
        client = LLMClient(provider="groq", model="test-model")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Fallback response"
        
        # Mock Groq to fail, OpenAI to succeed
        with patch.object(client, '_get_groq_client') as mock_get_groq:
            with patch.object(client, '_get_openai_client') as mock_get_openai:
                # Groq raises error
                mock_groq_client = AsyncMock()
                mock_groq_client.chat.completions.create = AsyncMock(side_effect=Exception("Groq error"))
                mock_get_groq.return_value = mock_groq_client
                
                # OpenAI succeeds
                mock_openai_client = AsyncMock()
                mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_get_openai.return_value = mock_openai_client
                
                result = await client.generate(
                    messages=[{"role": "user", "content": "Test"}],
                    use_fallback=True
                )
                
                assert result == "Fallback response"
                # Verify OpenAI was called
                mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_no_fallback(self):
        """Test that fallback is not used when disabled."""
        client = LLMClient(provider="groq", model="test-model")
        
        with patch.object(client, '_get_groq_client') as mock_get_client:
            mock_groq_client = AsyncMock()
            mock_groq_client.chat.completions.create = AsyncMock(side_effect=Exception("Groq error"))
            mock_get_client.return_value = mock_groq_client
            
            with pytest.raises(Exception, match="Groq error"):
                await client.generate(
                    messages=[{"role": "user", "content": "Test"}],
                    use_fallback=False
                )
    
    @pytest.mark.asyncio
    async def test_generate_all_providers_fail(self):
        """Test error when all providers fail."""
        client = LLMClient(provider="groq", model="test-model")
        
        # Mock all provider methods to fail
        with patch.object(client, '_generate_groq', side_effect=Exception("Groq error")):
            with patch.object(client, '_generate_openai', side_effect=Exception("OpenAI error")):
                with patch.object(client, '_generate_gpt4all', side_effect=Exception("GPT4All error")):
                    with pytest.raises(RuntimeError, match="All providers failed"):
                        await client.generate(
                            messages=[{"role": "user", "content": "Test"}],
                            use_fallback=True
                        )


class TestLLMClientProviders:
    """Test individual provider client creation."""
    
    def test_get_groq_client_missing_key(self):
        """Test Groq client raises error when API key is missing."""
        client = LLMClient(provider="groq")
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                client._get_groq_client()
    
    def test_get_openai_client_missing_key(self):
        """Test OpenAI client raises error when API key is missing."""
        client = LLMClient(provider="openai")
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                client._get_openai_client()
    
    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_gpt4all_client_model_not_found(self, mock_listdir, mock_exists, mock_isdir):
        """Test GPT4All client raises error when model file not found."""
        client = LLMClient(provider="gpt4all")
        mock_isdir.return_value = True
        mock_exists.return_value = False
        mock_listdir.return_value = []  # No model files
        
        with pytest.raises(RuntimeError, match="Failed to load GPT4All model"):
            client._get_gpt4all_client()


class TestGetLLMClient:
    """Test convenience function."""
    
    def test_get_llm_client_default(self):
        """Test convenience function returns client."""
        client = get_llm_client()
        assert isinstance(client, LLMClient)
    
    def test_get_llm_client_with_provider(self):
        """Test convenience function with provider."""
        client = get_llm_client(provider="openai")
        assert client.provider == "openai"
    
    def test_get_llm_client_with_model(self):
        """Test convenience function with model."""
        client = get_llm_client(provider="groq", model="custom-model")
        assert client.model == "custom-model"


class TestLLMProviderEnum:
    """Test LLMProvider enum."""
    
    def test_provider_enum_values(self):
        """Test provider enum has correct values."""
        assert LLMProvider.GROQ.value == "groq"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.GPT4ALL.value == "gpt4all"
