import requests
import logging
import platform
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_PORT = "11434"
LOCALHOST = "127.0.0.1"
DISCOVERY_TIMEOUT = 0.5
CONNECTION_TIMEOUT = 5


class HostDiscovery:
    """Interface for Ollama host discovery strategies."""
    
    def discover(self) -> str:
        """Discover the Ollama host."""
        raise NotImplementedError


class LocalhostDiscovery(HostDiscovery):
    """Discovery strategy that checks localhost first."""
    
    def __init__(self, timeout: float = DISCOVERY_TIMEOUT, port: str = DEFAULT_PORT):
        self.timeout = timeout
        self.port = port
    
    def discover(self) -> str:
        """
        Check if localhost is responsive.
        
        Returns:
            str: The discovered host (typically "127.0.0.1" or "localhost")
        """
        # Try standard localhost first
        try:
            if requests.get(f"http://{LOCALHOST}:{self.port}/api/tags", timeout=self.timeout).status_code == 200:
                logger.info("Connected to Ollama at 127.0.0.1")
                return LOCALHOST
        except Exception:
            pass
        
        # On Windows, try localhost as a fallback
        if platform.system() == "Windows":
            try:
                if requests.get(f"http://localhost:{self.port}/api/tags", timeout=self.timeout).status_code == 200:
                    logger.info("Connected to Ollama at localhost")
                    return "localhost"
            except Exception:
                pass
        
        # Final fallback
        logger.warning("Could not discover Ollama host, using localhost")
        return LOCALHOST


class OllamaClient:
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        host_discovery: Optional[HostDiscovery] = None,
        requests_client: Optional[requests.Session] = None,
        model: str = "llama3.1:8b"
    ):
        """
        Initialize Ollama client.
        
        Args:
            port: Ollama port number
            host_discovery: Optional host discovery strategy for testing
            requests_client: Optional requests session for testing
            model: Default model to use
        """
        self.port = port
        self.host_discovery = host_discovery or LocalhostDiscovery()
        self.requests_client = requests_client or requests.Session()
        self.model = model
        
        self.base_url = f"http://{self.host_discovery.discover()}:{self.port}"
        logger.info(f"Ollama Client initialized at: {self.base_url} with model: {model}")

    def check_connection(self) -> bool:
        """
        Returns True if Ollama is reachable and listening.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.requests_client.get(f"{self.base_url}/api/tags", timeout=CONNECTION_TIMEOUT)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.debug(f"Connection check failed: {e}")
            return False

    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt
            **kwargs: Additional parameters for the model
            
        Returns:
            dict: Response from Ollama or None if error
        """
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = self.requests_client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    def chat(self, messages: list, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate text using Ollama chat format.
        
        Args:
            messages: List of messages in format [{"role": "user", "content": "..."}]
            **kwargs: Additional parameters for the model
            
        Returns:
            dict: Response from Ollama or None if error
        """
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            response = self.requests_client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in chat: {e}")
            return None
    
    def list_models(self) -> Optional[list]:
        """
        List available models from Ollama.
        
        Returns:
            list: List of available models or None if error
        """
        endpoint = f"{self.base_url}/api/tags"
        
        try:
            response = self.requests_client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing models: {e}")
            return None
    
    def set_model(self, model: str) -> None:
        """
        Set the model to use for generation.
        
        Args:
            model: Model name
        """
        self.model = model
        logger.info(f"Model changed to: {model}")