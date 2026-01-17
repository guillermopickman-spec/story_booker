"""
LLM Client abstraction supporting multiple providers:
- Groq (primary, default)
- OpenAI (secondary)
- Local GPT4All (fallback)
"""

import asyncio
import json
import os
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OPENAI = "openai"
    GPT4ALL = "gpt4all"
    MOCK = "mock"


class LLMClient:
    """Unified LLM client that can switch between different providers."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client with specified provider.

        Args:
            provider: The LLM provider to use (groq, openai, gpt4all). Defaults to groq.
            model: Model name to use (defaults based on provider)
        """
        provider_str = provider or os.getenv("LLM_PROVIDER", "groq")
        provider_str = provider_str.lower().strip()
        if provider_str not in [p.value for p in LLMProvider]:
            raise ValueError(f"Unknown provider: {provider_str}. Must be one of: {[p.value for p in LLMProvider]}")
        self.provider = provider_str
        self.model = model or self._get_default_model()
        self._clients = {}
        
        # Log which provider is being used
        logger.info(f"LLMClient initialized: provider='{self.provider}', model='{self.model}'")
        if not provider:
            env_provider = os.getenv("LLM_PROVIDER", "NOT SET")
            logger.info(f"  Provider from environment: LLM_PROVIDER='{env_provider}'")
        
    def _get_default_model(self) -> str:
        """Get default model based on provider."""
        defaults = {
            "groq": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "gpt4all": os.getenv("GPT4ALL_MODEL_NAME", "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf")
        }
        return defaults.get(self.provider, defaults["groq"])
    
    def _get_groq_client(self):
        """Get or create Groq client."""
        if "groq" not in self._clients:
            try:
                from groq import AsyncGroq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError(
                        "GROQ_API_KEY not found in environment. "
                        "Please set GROQ_API_KEY in your .env file or environment variables."
                    )
                placeholder_values = ["your_groq_api_key_here", "your_api_key_here", ""]
                if api_key.lower() in [p.lower() for p in placeholder_values]:
                    raise ValueError(
                        "GROQ_API_KEY appears to be a placeholder value. "
                        "Please set a valid API key in your .env file."
                    )
                self._clients["groq"] = AsyncGroq(api_key=api_key)
            except ImportError:
                raise ImportError("groq package not installed. Install with: pip install groq")
        return self._clients["groq"]
    
    def _get_openai_client(self):
        """Get or create OpenAI client."""
        if "openai" not in self._clients:
            try:
                from openai import AsyncOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY not found in environment. "
                        "Please set OPENAI_API_KEY in your .env file or environment variables."
                    )
                placeholder_values = ["your_openai_api_key_here", "your_api_key_here", ""]
                if api_key.lower() in [p.lower() for p in placeholder_values]:
                    raise ValueError(
                        "OPENAI_API_KEY appears to be a placeholder value. "
                        "Please set a valid API key in your .env file."
                    )
                self._clients["openai"] = AsyncOpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        return self._clients["openai"]
    
    def _get_gpt4all_client(self):
        """Get or create GPT4All client."""
        if "gpt4all" not in self._clients:
            try:
                from gpt4all import GPT4All
                model_path = os.getenv("GPT4ALL_MODEL_PATH", r"C:\Users\Guill\AppData\Local\nomic.ai\GPT4All")
                model_name = os.getenv("GPT4ALL_MODEL_NAME", "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf")
                
                if os.path.isdir(model_path):
                    model_file_path = os.path.join(model_path, model_name)
                    if os.path.exists(model_file_path):
                        self._clients["gpt4all"] = GPT4All(model_name=model_name, model_path=model_path)
                    else:
                        available_models = [f for f in os.listdir(model_path) if f.endswith(('.gguf', '.bin'))]
                        if available_models:
                            raise FileNotFoundError(
                                f"Model '{model_name}' not found in {model_path}. "
                                f"Available models: {', '.join(available_models)}"
                            )
                        else:
                            raise FileNotFoundError(
                                f"No model files found in {model_path}. "
                                f"Expected model: {model_name}"
                            )
                else:
                    raise NotADirectoryError(f"Model path is not a directory: {model_path}")
            except ImportError:
                raise ImportError("gpt4all package not installed. Install with: pip install gpt4all")
            except Exception as e:
                raise RuntimeError(f"Failed to load GPT4All model: {e}")
        return self._clients["gpt4all"]
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None,
        temperature: float = 0.7,
        use_fallback: bool = True
    ) -> str:
        """
        Generate a response using the configured provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            response_format: Optional format specification (e.g., {"type": "json_object"})
            temperature: Sampling temperature (0.0 to 2.0)
            use_fallback: If True, try fallback providers on failure
            
        Returns:
            Generated text content
            
        Raises:
            asyncio.TimeoutError: If the operation exceeds the configured timeout
        """
        timeout_seconds = float(os.getenv("LLM_TIMEOUT", "120"))
        providers_to_try = [self.provider]
        
        if use_fallback:
            fallback_order = {
                "groq": ["openai", "gpt4all", "mock"],
                "openai": ["groq", "gpt4all", "mock"],
                "gpt4all": ["groq", "openai", "mock"],
                "mock": ["groq", "openai", "gpt4all"]
            }
            providers_to_try.extend(fallback_order.get(self.provider, []))
        
        last_error = None
        logger.info(f"LLM generation: primary provider='{self.provider}', fallback enabled={use_fallback}")
        if use_fallback:
            logger.info(f"  Fallback order: {providers_to_try}")
        
        for provider in providers_to_try:
            try:
                logger.info(f"Attempting LLM generation with provider: {provider}")
                if provider == "groq":
                    result = await asyncio.wait_for(
                        self._generate_groq(messages, response_format, temperature),
                        timeout=timeout_seconds
                    )
                    return result
                elif provider == "openai":
                    result = await asyncio.wait_for(
                        self._generate_openai(messages, response_format, temperature),
                        timeout=timeout_seconds
                    )
                    return result
                elif provider == "gpt4all":
                    result = await asyncio.wait_for(
                        self._generate_gpt4all(messages, temperature, response_format),
                        timeout=timeout_seconds
                    )
                    return result
                elif provider == "mock":
                    result = await asyncio.wait_for(
                        self._generate_mock(messages, response_format),
                        timeout=timeout_seconds
                    )
                    logger.info(f"Successfully generated response using provider: {provider}")
                    return result
            except asyncio.TimeoutError:
                timeout_msg = f"LLM generation timed out after {timeout_seconds}s using provider '{provider}'"
                last_error = TimeoutError(timeout_msg)
                logger.warning(f"Provider '{provider}' timed out. Trying next provider...")
                if provider == providers_to_try[-1]:
                    raise last_error
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"Provider '{provider}' failed: {type(e).__name__}: {str(e)[:100]}. Trying next provider...")
                if provider == providers_to_try[-1]:
                    raise
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    async def _generate_groq(self, messages: List[Dict[str, str]], response_format: Optional[Dict], temperature: float) -> str:
        """Generate using Groq."""
        client = self._get_groq_client()
        
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if response_format and response_format.get("type") == "json_object":
            request_params["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    async def _generate_openai(self, messages: List[Dict[str, str]], response_format: Optional[Dict], temperature: float) -> str:
        """Generate using OpenAI."""
        client = self._get_openai_client()
        
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if response_format:
            request_params["response_format"] = response_format
        
        response = await client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    async def _generate_gpt4all(self, messages: List[Dict[str, str]], temperature: float, response_format: Optional[Dict[str, str]] = None) -> str:
        """Generate using local GPT4All (synchronous, needs to be wrapped)."""
        import asyncio
        
        client = self._get_gpt4all_client()
        
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        
        # GPT4All doesn't support response_format natively, so add JSON instruction to prompt if needed
        if response_format and response_format.get("type") == "json_object":
            prompt = prompt.rstrip() + "\n\nIMPORTANT: You MUST respond with valid JSON only. Do not include any text before or after the JSON. Return only the JSON object."
        
        # Estimate tokens: GPT4All tokenizer is more aggressive, use ~3.3 chars per token
        prompt_chars = len(prompt)
        estimated_tokens = int(prompt_chars / 3.3)  # More accurate for GPT4All
        
        # Truncate prompt if it exceeds 2048 tokens
        # Using 3.3 chars/token estimate which is more accurate for GPT4All
        if estimated_tokens > 1900:  # Conservative buffer (leave ~150 tokens)
            # Try to truncate user message while keeping system
            system_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "system"), "")
            user_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "user"), "")
            
            # Calculate how much we can keep
            # Target ~1800 tokens max (conservative), using 3.3 chars/token
            system_chars = len(system_msg)
            max_total_chars = int(1800 * 3.3)  # ~5940 chars for ~1800 tokens
            max_user_chars = max_total_chars - system_chars - 300  # Leave buffer
            
            if len(user_msg) > max_user_chars:
                # Truncate user message, keeping the beginning (most important info)
                user_msg = user_msg[:max_user_chars] + "\n\n[Content truncated due to token limit]"
                prompt_parts = []
                prompt_parts.append(f"System: {system_msg}")
                prompt_parts.append(f"User: {user_msg}")
                prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.generate(prompt, temp=temperature, max_tokens=2000)
        )
        
        return response
    
    async def _generate_mock(self, messages: List[Dict[str, str]], response_format: Optional[Dict]) -> str:
        """Generate using mock provider (for testing without API calls)."""
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content")
                if content:
                    user_message = str(content)
                break
        
        if response_format and response_format.get("type") == "json_object":
            theme = user_message if user_message else "adventure"
            num_beats = 5
            if user_message:
                user_lower = user_message.lower()
                if "exactly" in user_lower and "beats" in user_lower:
                    import re
                    match = re.search(r'exactly\s+(\d+)', user_lower)
                    if match:
                        num_beats = int(match.group(1))
            
            beats = []
            for i in range(num_beats):
                beats.append({
                    "text": f"Paragraph 1 for beat {i+1} about {theme}.\n\nParagraph 2 for beat {i+1} continuing the story.",
                    "visual_description": f"Scene {i+1} showing {theme}",
                    "sticker_subjects": [f"subject_{i+1}_a", f"subject_{i+1}_b"]
                })
            
            mock_response = {
                "title": f"The Story of {theme.title()}",
                "beats": beats
            }
            return json.dumps(mock_response)
        else:
            return f"Mock LLM response for: {user_message or 'test'}"
    
    async def close(self):
        """Close all async client connections."""
        for provider, client in self._clients.items():
            try:
                if hasattr(client, 'close'):
                    if asyncio.iscoroutinefunction(client.close):
                        await client.close()
                    else:
                        client.close()
            except Exception as e:
                # Log but don't raise - we want to close all clients even if one fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error closing {provider} client: {e}")
        self._clients.clear()


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    """Get an LLM client instance."""
    return LLMClient(provider=provider, model=model)
