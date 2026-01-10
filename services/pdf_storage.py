"""
PDF Storage: Manages file system operations for storing generated PDF storybooks.
"""

import os
from pathlib import Path
from typing import Optional


def ensure_output_directory() -> Path:
    """
    Ensure the output directory exists.
    
    Returns:
        Path object for the output directory
    """
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_pdf_path(job_id: str) -> Path:
    """
    Get the file path for a PDF storybook.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Path object for the PDF file
    """
    output_dir = ensure_output_directory()
    filename = f"{job_id}.pdf"
    return output_dir / filename


def save_pdf(job_id: str, pdf_data: bytes) -> str:
    """
    Save PDF data to file.
    
    Args:
        job_id: Unique job identifier
        pdf_data: PDF file bytes
        
    Returns:
        String path to saved PDF file (absolute path)
    """
    pdf_path = get_pdf_path(job_id)
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf_data)
    
    return str(pdf_path.absolute())


def get_pdf_path_string(job_id: str) -> str:
    """
    Get the PDF file path as a string (for JobStatus.file_path).
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Absolute path string to PDF file (even if it doesn't exist yet)
    """
    pdf_path = get_pdf_path(job_id)
    return str(pdf_path.absolute())


def pdf_exists(job_id: str) -> bool:
    """
    Check if a PDF file exists for a job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        True if PDF file exists, False otherwise
    """
    pdf_path = get_pdf_path(job_id)
    return pdf_path.exists()


def delete_pdf(job_id: str):
    """
    Delete a PDF file for a job (cleanup function).
    
    Args:
        job_id: Unique job identifier
    """
    pdf_path = get_pdf_path(job_id)
    if pdf_path.exists():
        pdf_path.unlink()
