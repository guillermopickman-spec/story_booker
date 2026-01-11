"""
API endpoint tests for Story Booker.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app, jobs

# Clear jobs dictionary before each test
@pytest.fixture(autouse=True)
def clear_jobs():
    """Clear the jobs dictionary before each test."""
    jobs.clear()
    yield
    jobs.clear()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Story Booker API"
    assert data["version"] == "0.1.0"
    assert data["description"] == "AI Sticker-Book Generator"


def test_generate_job_creates_job(client):
    """Test POST /generate creates a new job and returns job_id."""
    response = client.post("/generate")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)
    assert len(data["job_id"]) > 0


def test_generate_job_with_theme(client):
    """Test POST /generate accepts optional theme parameter."""
    response = client.post("/generate?theme=adventure")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


def test_generate_job_initializes_status(client):
    """Test that generated job is initialized with correct status."""
    response = client.post("/generate")
    job_id = response.json()["job_id"]
    
    status_response = client.get(f"/status/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "pending"
    assert status_data["progress"] == 0
    assert status_data["file_path"] is None


def test_get_status_existing_job(client):
    """Test GET /status/{job_id} returns correct status for existing job."""
    # Create a job first
    create_response = client.post("/generate")
    job_id = create_response.json()["job_id"]
    
    # Get its status
    status_response = client.get(f"/status/{job_id}")
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "pending"


def test_get_status_not_found(client):
    """Test GET /status/{job_id} returns 404 for non-existent job."""
    response = client.get("/status/non-existent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_status_invalid_uuid_format(client):
    """Test GET /status/{job_id} handles invalid UUID format."""
    response = client.get("/status/invalid-uuid-format")
    assert response.status_code == 404


def test_multiple_jobs_are_independent(client):
    """Test that multiple jobs can be created and tracked independently."""
    # Create two jobs
    response1 = client.post("/generate")
    job_id1 = response1.json()["job_id"]
    
    response2 = client.post("/generate")
    job_id2 = response2.json()["job_id"]
    
    # Verify they are different
    assert job_id1 != job_id2
    
    # Verify both exist and have correct status
    status1 = client.get(f"/status/{job_id1}").json()
    status2 = client.get(f"/status/{job_id2}").json()
    
    assert status1["job_id"] == job_id1
    assert status2["job_id"] == job_id2
    assert status1["status"] == "pending"
    assert status2["status"] == "pending"


def test_download_not_found_invalid_job_id(client):
    """Test GET /download/{job_id} returns 404 for non-existent job."""
    response = client.get("/download/non-existent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_not_ready_pending_status(client):
    """Test GET /download/{job_id} returns 404 when job is not completed."""
    # Create a job
    create_response = client.post("/generate")
    job_id = create_response.json()["job_id"]
    
    # Try to download (should fail since status is "pending")
    download_response = client.get(f"/download/{job_id}")
    assert download_response.status_code == 404
    assert "not completed" in download_response.json()["detail"].lower()


def test_download_not_ready_no_file_path(client):
    """Test GET /download/{job_id} returns 404 when job has no file_path."""
    # Create a job and manually set status to completed without file_path
    create_response = client.post("/generate")
    job_id = create_response.json()["job_id"]
    
    # Manually update job status (simulating completed but missing file)
    jobs[job_id].status = "completed"
    jobs[job_id].file_path = None
    
    # Try to download
    download_response = client.get(f"/download/{job_id}")
    assert download_response.status_code == 404
    assert "file not found" in download_response.json()["detail"].lower()


def test_job_status_structure(client):
    """Test that JobStatus response has correct structure and types."""
    create_response = client.post("/generate")
    job_id = create_response.json()["job_id"]
    
    status_response = client.get(f"/status/{job_id}")
    data = status_response.json()
    
    # Verify all expected fields exist
    assert "job_id" in data
    assert "status" in data
    assert "file_path" in data
    assert "progress" in data
    
    # Verify types
    assert isinstance(data["job_id"], str)
    assert isinstance(data["status"], str)
    assert isinstance(data["file_path"], (type(None), str))
    assert isinstance(data["progress"], (type(None), int))
    
    # Verify status is one of expected values
    assert data["status"] in ["pending", "processing", "completed", "failed"]
