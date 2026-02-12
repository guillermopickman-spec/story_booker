import unittest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.characters.image_gen.client import (
    ComfyClient,
    HostDiscovery,
    LocalhostDiscovery,
    DEFAULT_PORT,
    LOCALHOST,
    CONNECTION_TIMEOUT
)


class TestHostDiscoveryInterface(unittest.TestCase):
    """Test the abstract HostDiscovery interface."""
    
    def test_host_discovery_raises_not_implemented(self):
        """Test that the abstract base class raises NotImplementedError."""
        discovery = HostDiscovery()
        with self.assertRaises(NotImplementedError):
            discovery.discover()


class TestLocalhostDiscovery(unittest.TestCase):
    """Test the LocalhostDiscovery strategy."""
    
    def setUp(self):
        self.discovery = LocalhostDiscovery(timeout=0.5)
    
    @patch('modules.characters.image_gen.client.requests')
    def test_discover_localhost_success(self, mock_requests):
        """Test discovering localhost when it's responsive."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        # Execute
        result = self.discovery.discover()
        
        # Verify
        mock_requests.get.assert_called_once_with(f"http://{LOCALHOST}:8188", timeout=0.5)
        self.assertEqual(result, LOCALHOST)
    
    @patch('modules.characters.image_gen.client.requests')
    @patch('modules.characters.image_gen.client.platform')
    def test_discover_localhost_failure_then_wsl_gateway(self, mock_platform, mock_requests):
        """Test discovering WSL gateway when localhost fails."""
        # Mock platform as Linux
        mock_platform.system.return_value = "Linux"
        
        # Setup mock - localhost fails
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        # Mock subprocess for WSL gateway
        with patch('modules.characters.image_gen.client.subprocess') as mock_subprocess:
            mock_ip = b"172.28.0.1"
            mock_subprocess.check_output.return_value = mock_ip
            
            # Execute
            result = self.discovery.discover()
            
            # Verify
            self.assertEqual(result, "172.28.0.1")
    
    @patch('modules.characters.image_gen.client.requests')
    @patch('modules.characters.image_gen.client.platform')
    def test_discover_wsl_gateway_fallback(self, mock_platform, mock_requests):
        """Test falling back to hardcoded WSL gateway."""
        # Mock platform as Linux
        mock_platform.system.return_value = "Linux"
        
        # Setup mock - localhost fails
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        # Mock subprocess to raise exception
        with patch('modules.characters.image_gen.client.subprocess') as mock_subprocess:
            mock_subprocess.check_output.side_effect = subprocess.CalledProcessError(1, "ip route")
            
            # Execute
            result = self.discovery.discover()
            
            # Verify - should return hardcoded fallback
            self.assertEqual(result, "172.22.144.1")


class TestComfyClient(unittest.TestCase):
    """Test the ComfyClient class."""
    
    def setUp(self):
        self.mock_discovery = Mock(spec=HostDiscovery)
        self.mock_discovery.discover.return_value = "127.0.0.1"
        
        self.mock_requests = Mock(spec=requests.Session)
        self.client = ComfyClient(
            port="8188",
            host_discovery=self.mock_discovery,
            requests_client=self.mock_requests
        )
    
    def test_initialization_with_dependencies(self):
        """Test client initialization with custom dependencies."""
        self.assertEqual(self.client.port, "8188")
        self.assertEqual(self.client.base_url, "http://127.0.0.1:8188")
        self.assertEqual(self.client.host_discovery, self.mock_discovery)
        self.assertEqual(self.client.requests_client, self.mock_requests)
    
    def test_initialization_defaults(self):
        """Test client initialization uses defaults when not specified."""
        with patch('modules.characters.image_gen.client.LocalhostDiscovery') as mock_discovery_class:
            mock_discovery_instance = Mock(spec=LocalhostDiscovery)
            mock_discovery_instance.discover.return_value = LOCALHOST
            mock_discovery_class.return_value = mock_discovery_instance
            
            default_client = ComfyClient()
            self.assertEqual(default_client.port, DEFAULT_PORT)
            self.assertIsInstance(default_client.host_discovery, LocalhostDiscovery)
            self.assertIsInstance(default_client.requests_client, requests.Session)
            self.assertEqual(default_client.base_url, f"http://{LOCALHOST}:{DEFAULT_PORT}")
    
    def test_check_connection_success(self):
        """Test successful connection check."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_requests.get.return_value = mock_response
        
        # Execute
        result = self.client.check_connection()
        
        # Verify
        self.assertTrue(result)
        self.mock_requests.get.assert_called_once()
        # Check that timeout is used
        call_kwargs = self.mock_requests.get.call_args[1]
        self.assertEqual(call_kwargs['timeout'], CONNECTION_TIMEOUT)
    
    def test_check_connection_failure_no_server(self):
        """Test connection check fails when server is not running."""
        # Setup mock - connection raises exception
        self.mock_requests.get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Execute
        result = self.client.check_connection()
        
        # Verify
        self.assertFalse(result)
    
    def test_check_connection_http_error(self):
        """Test connection check handles HTTP errors."""
        # Setup mock - HTTP error
        self.mock_requests.get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        # Execute
        result = self.client.check_connection()
        
        # Verify
        self.assertFalse(result)
    
    def test_check_connection_timeout(self):
        """Test connection check handles timeouts."""
        # Setup mock - timeout
        self.mock_requests.get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Execute
        result = self.client.check_connection()
        
        # Verify
        self.assertFalse(result)
    
    def test_queue_prompt_success(self):
        """Test successful prompt queueing."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"prompt_id": "12345"}
        mock_response.raise_for_status = Mock()
        self.mock_requests.post.return_value = mock_response
        
        workflow = {"prompt": {"some": "workflow"}}
        
        # Execute
        result = self.client.queue_prompt(workflow)
        
        # Verify
        self.assertEqual(result, {"prompt_id": "12345"})
        self.mock_requests.post.assert_called_once()
        
        # Check endpoint and payload
        call_args = self.mock_requests.post.call_args
        self.assertEqual(call_args[0][0], "http://127.0.0.1:8188/prompt")
        self.assertEqual(call_args[1]['json'], {"prompt": workflow})
    
    def test_queue_prompt_http_error(self):
        """Test prompt queueing handles HTTP errors."""
        # Setup mock - HTTP error
        self.mock_requests.post.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        workflow = {"prompt": {"some": "workflow"}}
        
        # Execute
        result = self.client.queue_prompt(workflow)
        
        # Verify
        self.assertIsNone(result)
    
    def test_queue_prompt_connection_error(self):
        """Test prompt queueing handles connection errors."""
        # Setup mock - connection error
        self.mock_requests.post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        workflow = {"prompt": {"some": "workflow"}}
        
        # Execute
        result = self.client.queue_prompt(workflow)
        
        # Verify
        self.assertIsNone(result)
    
    def test_queue_prompt_timeout(self):
        """Test prompt queueing handles timeouts."""
        # Setup mock - timeout
        self.mock_requests.post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        workflow = {"prompt": {"some": "workflow"}}
        
        # Execute
        result = self.client.queue_prompt(workflow)
        
        # Verify
        self.assertIsNone(result)
    
    def test_check_connection_non_http_success(self):
        """Test connection check handles non-200 HTTP status codes."""
        # Setup mock - HTTP 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        self.mock_requests.get.return_value = mock_response
        
        # Execute
        result = self.client.check_connection()
        
        # Verify - should return False for non-200 status
        self.assertFalse(result)
    
    def test_queue_prompt_with_custom_port(self):
        """Test client initialization with custom port."""
        with patch('modules.characters.image_gen.client.LocalhostDiscovery') as mock_discovery:
            mock_discovery.return_value.discover.return_value = LOCALHOST
            custom_client = ComfyClient(port="9000")
            self.assertEqual(custom_client.port, "9000")
            self.assertEqual(custom_client.base_url, f"http://{LOCALHOST}:9000")
    
    def test_requests_client_post_called_with_json(self):
        """Verify post is called with json parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"prompt_id": "test-id"}
        mock_response.raise_for_status = Mock()
        self.mock_requests.post.return_value = mock_response
        
        workflow = {"prompt": {"test": "workflow"}}
        self.client.queue_prompt(workflow)
        
        # Verify json parameter was passed
        call_args = self.mock_requests.post.call_args
        self.assertIn('json', call_args[1])
        self.assertEqual(call_args[1]['json'], {"prompt": workflow})
    
    def test_base_url_uses_discovered_host(self):
        """Test base_url uses the host returned by discovery."""
        # Create a mock discovery that returns a specific IP
        mock_discovery = Mock(spec=HostDiscovery)
        mock_discovery.discover.return_value = "192.168.1.100"
        
        # Create client with the mock discovery
        client = ComfyClient(
            port="8188",
            host_discovery=mock_discovery,
            requests_client=self.mock_requests
        )
        
        # The base_url should reflect the discovered host
        self.assertEqual(client.base_url, "http://192.168.1.100:8188")


if __name__ == '__main__':
    unittest.main()
