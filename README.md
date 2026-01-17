# 📚 Story Booker - AI-Powered Storybook Generator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

**Enterprise-grade AI storybook generation platform for commercial publishing**

Generate professional, print-ready children's storybooks with AI-generated narratives and illustrations

[Features](#-features) • [Technology Stack](#-technology-stack) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Testing](#-testing)

</div>

---

## 🎯 Overview

**Story Booker** is a sophisticated, production-ready FastAPI application that transforms simple story themes into complete, professionally-formatted children's storybooks. Built with enterprise architecture principles, it combines cutting-edge AI technologies to deliver commercial-grade PDF outputs suitable for print-on-demand publishing platforms like Amazon KDP.

### Key Capabilities

- **AI-Powered Narrative Generation**: Multi-provider LLM integration (Groq, OpenAI, GPT4All) for high-quality story creation
- **Intelligent Image Generation**: Advanced image synthesis via Pollinations.ai and OpenAI DALL-E with character consistency
- **Character Visual DNA System**: Maintains visual consistency across all story pages using reference images and seed locking
- **Print-on-Demand Ready**: CMYK color conversion, bleed margins, and KDP-compliant PDF generation
- **Multi-Language Support**: Generate storybooks in multiple languages (English, Spanish, and extensible)
- **Production Architecture**: Asynchronous processing, job queue management, error handling, and comprehensive logging

Perfect for content creators, educators, publishers, and developers who need scalable, reliable storybook generation with commercial publishing standards.

---

## ✨ Features

### Core Generation Features

- 🧠 **Multi-Provider LLM Support**
  - **Groq**: Lightning-fast inference with free tier (Llama 3.3 70B)
  - **OpenAI**: High-quality GPT-4o-mini for premium results
  - **GPT4All**: Local/offline processing for privacy-sensitive workflows
  - **Automatic Fallback**: Seamless failover between providers for maximum reliability
  - **Custom Timeouts**: Configurable per-provider timeout handling

- 🎨 **Advanced Image Generation**
  - **Pollinations.ai Integration**: Authenticated API access for high-quality illustrations
  - **OpenAI DALL-E Support**: Premium image generation option
  - **Style Templates**: 6 built-in art styles (CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART)
  - **Full-Page Illustrations**: Complete scene artwork per story page
  - **Cover Generation**: Automated cover image creation with title overlay

- 🎭 **Character Consistency System**
  - **Character Extraction**: Automatic identification of main characters from stories
  - **Visual DNA Locking**: Seed-based image generation for consistent character appearance
  - **Reference Image Generation**: Character concept art for visual consistency
  - **Cross-Page Continuity**: Ensures characters look identical across all pages
  - **Physical Attribute Tracking**: Detailed character descriptions maintained throughout

- 📐 **Intelligent Layout Engine**
  - **Dynamic Grid System**: Adaptive layouts for 1-3 images per page
  - **Random Rotations**: Natural sticker-style placement (-10° to +10°)
  - **Responsive Text Wrapping**: Smart text placement around images
  - **Full-Page Backgrounds**: Seamless full-bleed illustrations
  - **Multi-Trim Size Support**: Square (8.5×8.5"), Standard (8.5×11"), Landscape (11×8.5")

- 🖨️ **Print-on-Demand (POD) Preflight**
  - **CMYK Color Conversion**: Automatic RGB→CMYK conversion for print accuracy
  - **Bleed Margins**: 0.125" (9pt) bleeds on all sides for KDP compliance
  - **Trim Size Management**: Industry-standard dimensions with safe zones
  - **Color Profile Embedding**: ICC color profiles for accurate reproduction
  - **KDP Validation**: Pre-upload quality checks for Amazon KDP requirements

- 🌍 **Multi-Language Support**
  - **Bilingual Generation**: English and Spanish with extensible architecture
  - **Shared Visual Assets**: Images generated once, reused across language variants
  - **Language-Specific Storytelling**: Culturally appropriate narrative generation
  - **Per-Language PDFs**: Separate PDF output for each language

- 📊 **Job Management System**
  - **UUID-Based Tracking**: Unique job identifiers for all operations
  - **Real-Time Progress**: 0-100% progress tracking with detailed step information
  - **Status Monitoring**: Pending → Processing → Completed/Failed state machine
  - **Error Reporting**: Comprehensive error messages with full tracebacks
  - **Background Processing**: Asynchronous job execution via FastAPI BackgroundTasks

### Technical Features

- ⚡ **Fully Asynchronous**: Built on Python asyncio for optimal performance
- 🔄 **Provider Fallback**: Automatic failover between LLM and image providers
- 🧪 **Comprehensive Testing**: Unit tests, integration tests, and end-to-end validation
- 📦 **Modular Architecture**: Clean service-based design with separation of concerns
- 🔐 **Secure Configuration**: Environment-based secrets management with `.env` files
- 📝 **Type Safety**: Full Pydantic model validation for data integrity
- 🚀 **Production Ready**: Error handling, logging, timeout management, and graceful degradation
- 📁 **File Management**: Organized asset storage with job-based directory structure
- 🔍 **Detailed Logging**: Structured logging for debugging and monitoring

---

## 🛠️ Technology Stack

### Core Framework & Runtime

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **Python** | 3.11+ | Runtime environment | PSF License |
| **FastAPI** | ≥0.104.0 | Async web framework & API | MIT |
| **Uvicorn** | ≥0.24.0 | ASGI server with standard extras | BSD |
| **Pydantic** | ≥2.0.0 | Data validation & serialization | MIT |

### AI & Machine Learning

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **OpenAI** | ≥1.0.0 | GPT models & DALL-E image generation | MIT |
| **Groq** | ≥0.4.0 | Fast LLM inference (Llama 3.3 70B) | Apache 2.0 |
| **GPT4All** | ≥2.5.0 | Local/offline LLM processing | MIT |
| **Pollinations** | ≥0.4.0 | Image generation API client | MIT |

### Image Processing

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **Pillow (PIL)** | ≥10.0.0 | Image manipulation, format conversion, CMYK support | HPND |
| **ImageCms** | (Pillow) | ICC color profile management | HPND |

### PDF Generation

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **FPDF2** | ≥2.7.0 | PDF document creation & layout | LGPL |
| **ReportLab** | ≥4.0.0 | Advanced PDF features & POD support | BSD |

### HTTP & Networking

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **httpx** | ≥0.24.0 | Async HTTP client for API calls | MIT |
| **requests** | ≥2.31.0 | Synchronous HTTP requests (fallback) | Apache 2.0 |

### Configuration & Environment

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **python-dotenv** | ≥1.0.0 | Environment variable management | BSD |

### Testing Framework

| Technology | Version | Purpose | License |
|-----------|---------|---------|---------|
| **pytest** | ≥7.4.0 | Testing framework | MIT |
| **pytest-asyncio** | ≥1.3.0 | Async test support | Apache 2.0 |

### Standard Library Dependencies

- `asyncio`: Asynchronous programming
- `json`: JSON serialization/deserialization
- `logging`: Structured logging system
- `pathlib`: Modern file path handling
- `uuid`: Unique identifier generation
- `io`: Byte stream handling
- `typing`: Type hints and annotations
- `enum`: Enumeration types
- `os`: Operating system interface
- `sys`: System-specific parameters
- `traceback`: Exception traceback utilities
- `hashlib`: Cryptographic hashing
- `re`: Regular expression operations
- `math`: Mathematical functions

### Development Tools

- **pytest.ini**: Test configuration with asyncio auto-mode
- **.env.example**: Environment variable template
- **requirements.txt**: Pinned dependency versions

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (src/main.py)                             │  │
│  │  - POST /generate  - GET /status  - GET /download    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Job Processing Layer                                 │  │
│  │  - Background task management                         │  │
│  │  - Progress tracking                                  │  │
│  │  - Error handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌──────▼──────────┐
│  LLM Services  │  │ Image Services  │  │  PDF Services   │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

### Service Layer Architecture

#### Core Services

1. **`llm_client.py`** - Multi-Provider LLM Client
   - Unified interface for Groq, OpenAI, and GPT4All
   - Provider fallback logic
   - Timeout and error handling
   - Async request management

2. **`author_agent.py`** - Story Generation Agent
   - Theme-based story generation
   - Multi-page story structure
   - Language-specific narrative generation
   - Story beat extraction

3. **`art_director_agent.py`** - Image Prompt Generation
   - Visual description enhancement
   - Style template application
   - Character-aware prompt generation
   - Background scene generation

4. **`character_service.py`** - Character Consistency System
   - Main character extraction from stories
   - Physical attribute tracking
   - Reference image generation
   - Visual DNA (seed) management
   - Cross-page character matching

5. **`image_service.py`** - Multi-Provider Image Generation
   - Pollinations.ai integration
   - OpenAI DALL-E support
   - Async image generation
   - Size and quality management

6. **`background_remover.py`** - Image Processing
   - Automatic background removal
   - Auto-cropping with padding
   - Transparency handling
   - Alpha channel management

7. **`sticker_generator.py`** - Sticker Processing Pipeline
   - Sticker-style image processing
   - Border addition (optional)
   - Format optimization

8. **`pdf_generator.py`** - PDF Layout & Generation
   - Page layout engine
   - Grid-based image placement
   - Text overlay and wrapping
   - Cover and back cover generation
   - About the Author page support

9. **`pod_preflight.py`** - Print-on-Demand Preflight
   - RGB to CMYK conversion
   - Bleed margin calculation
   - Trim size management
   - KDP validation checks
   - Color profile embedding

10. **`image_storage.py`** - Image File Management
    - Job-based directory structure
    - Asset organization
    - File path management

11. **`pdf_storage.py`** - PDF File Management
    - PDF file storage
    - Language-specific file naming
    - Output directory management

### Data Models (`src/models.py`)

- **`StoryBeat`**: Single story page with text, visual description, and sticker subjects
- **`Character`**: Character definition with physical attributes, reference images, and seeds
- **`StoryBook`**: Complete book structure with title, beats, characters, synopsis, and metadata
- **`JobStatus`**: Job tracking with status, progress, file paths, and error information
- **`ImagePrompt`**: Image generation prompt with subject information

### Request Flow

```
1. POST /generate
   ├─> Create JobStatus (pending)
   ├─> Background task: process_storybook_job()
   │   ├─> Generate story (first language)
   │   ├─> Extract characters
   │   ├─> Generate character reference images
   │   ├─> Generate cover image
   │   ├─> Generate image prompts for all beats
   │   ├─> Generate full-page images (shared across languages)
   │   ├─> For each language:
   │   │   ├─> Generate story content
   │   │   ├─> Generate PDF
   │   │   └─> Save PDF file
   │   └─> Update JobStatus (completed)
   │
2. GET /status/{job_id}
   └─> Return current JobStatus

3. GET /download/{job_id}
   └─> Return PDF file (FileResponse)
```

---

## 📦 Installation

### Prerequisites

- **Python 3.11 or higher** (3.12+ recommended for optimal performance)
- **pip** package manager
- **Virtual environment** (strongly recommended)
- **API Keys**:
  - Pollinations.ai API key (required for image generation)
  - Groq API key (recommended for fast LLM inference)
  - OpenAI API key (optional, for premium features)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/guillermopickman-spec/story_booker_v0.1.git
cd story_booker_v0.1
```

#### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your API keys
```

**Minimum Required Configuration:**
```bash
POLLINATIONS_API_KEY=your_pollinations_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

#### 5. Verify Installation

```bash
# Run quick test (no API calls)
python tests/test_quick_demo.py

# Should complete in ~4 seconds
```

#### 6. Start the Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. Access the API

- **API Base URL**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

---

## ⚙️ Configuration

### Environment Variables Reference

#### LLM Configuration

```bash
# Primary LLM Provider: groq, openai, or gpt4all
LLM_PROVIDER=groq

# Groq Configuration (Recommended - Fast & Free)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI Configuration (Optional - High Quality)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# GPT4All Configuration (Optional - Local/Offline)
GPT4ALL_MODEL_PATH=C:\Users\YourUser\AppData\Local\nomic.ai\GPT4All
GPT4ALL_MODEL_NAME=Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf
```

#### Image Generation Configuration

```bash
# Image Provider: pollinations or openai
IMAGE_PROVIDER=pollinations

# Pollinations.ai (Required - Default)
POLLINATIONS_API_KEY=your_pollinations_api_key_here

# OpenAI DALL-E (Optional - Uses OPENAI_API_KEY)
# IMAGE_PROVIDER=openai
```

#### Timeout Configuration

```bash
# Timeouts in seconds
LLM_TIMEOUT=120      # LLM API calls
IMAGE_TIMEOUT=180    # Image generation calls
```

#### Image Processing Configuration

```bash
# Background removal threshold (0-255, higher = more aggressive)
BG_REMOVAL_THRESHOLD=240

# Auto-crop padding in pixels
AUTOCROP_PADDING=10

# Enable sticker border (true/false)
ENABLE_STICKER_BORDER=false
STICKER_BORDER_WIDTH=3
```

#### PDF Generation Configuration

```bash
# Page size: letter, square, custom
PDF_PAGE_SIZE=letter

# Margins and layout
PDF_MARGIN=10
PDF_HEADER_HEIGHT=50
PDF_FOOTER_HEIGHT=150

# Sticker rotation range (degrees)
STICKER_ROTATION_MIN=-10
STICKER_ROTATION_MAX=10
```

#### Art Style Configuration

```bash
# Default art style: CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART
DEFAULT_ART_STYLE=3D_RENDERED
```

#### Testing Configuration

```bash
# Use mock providers for testing (no API calls)
USE_MOCK_PROVIDER=false
```

### API Key Acquisition

1. **Pollinations.ai API Key** (Required)
   - Visit: https://enter.pollinations.ai
   - Sign up for an account
   - Generate API key from dashboard
   - Add to `.env`: `POLLINATIONS_API_KEY=your_key`

2. **Groq API Key** (Recommended)
   - Visit: https://console.groq.com
   - Create account (free tier available)
   - Generate API key from API Keys section
   - Add to `.env`: `GROQ_API_KEY=your_key`

3. **OpenAI API Key** (Optional)
   - Visit: https://platform.openai.com/api-keys
   - Create account and add payment method
   - Generate API key
   - Add to `.env`: `OPENAI_API_KEY=your_key`

---

## 🚀 Usage

### API Endpoints

#### `POST /generate` - Create Storybook Generation Job

Initiates a new storybook generation job with specified parameters.

**Query Parameters:**
- `theme` (optional, string): Story theme (e.g., "a brave little mouse goes on an adventure")
- `num_pages` (optional, int): Number of pages/beats (1-10, default: 5)
- `style` (optional, string): Art style (CLAYMATION, VINTAGE_SKETCH, FLAT_DESIGN, 3D_RENDERED, WATERCOLOR, LINE_ART)
- `languages` (optional, list): List of language codes (e.g., ["en"], ["es"], ["en", "es"])
- `pod_ready` (optional, bool): Enable POD-ready PDF generation with CMYK and bleeds

**Example Request:**
```bash
curl -X POST "http://localhost:8000/generate?theme=a%20brave%20mouse&num_pages=5&style=CLAYMATION&pod_ready=true&languages=en"
```

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `GET /status/{job_id}` - Get Job Status

Retrieves the current status and progress of a generation job.

**Path Parameters:**
- `job_id` (string): Unique job identifier from `/generate` response

**Example Request:**
```bash
curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
```

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 65,
  "current_step": "Generating full-page image for beat 3/5",
  "file_path": null,
  "file_paths": null,
  "error_message": null
}
```

**Status Values:**
- `pending`: Job created, queued for processing
- `processing`: Job actively generating storybook
- `completed`: Job finished successfully ✅
- `failed`: Job encountered an error ❌

#### `GET /download/{job_id}` - Download Generated PDF

Downloads the completed PDF storybook file.

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Example Request:**
```bash
curl -O "http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000"
```

**Response:** PDF file with `Content-Type: application/pdf` and filename `storybook_{job_id}.pdf`

#### `GET /` - API Information

Returns basic API information and version.

**Response:**
```json
{
  "name": "Story Booker API",
  "version": "0.1.0",
  "description": "AI Sticker-Book Generator"
}
```

### Python Client Examples

#### Basic Single-Book Generation

```python
import httpx
import asyncio

async def generate_storybook():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        # Create generation job
        response = await client.post(
            f"{base_url}/generate",
            params={
                "theme": "a magical forest adventure",
                "num_pages": 3,
                "style": "CLAYMATION",
                "pod_ready": True,
                "languages": ["en"]
            }
        )
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"✅ Job created: {job_id}")
        
        # Monitor progress
        while True:
            status_response = await client.get(f"{base_url}/status/{job_id}")
            status = status_response.json()
            
            print(f"📊 Progress: {status['progress']}% - {status['current_step']}")
            
            if status["status"] == "completed":
                # Download PDF
                pdf_response = await client.get(f"{base_url}/download/{job_id}")
                filename = f"storybook_{job_id}.pdf"
                with open(filename, "wb") as f:
                    f.write(pdf_response.content)
                print(f"✅ PDF saved: {filename}")
                break
            elif status["status"] == "failed":
                print(f"❌ Error: {status['error_message']}")
                break
            
            await asyncio.sleep(2)

asyncio.run(generate_storybook())
```

#### Multi-Language Generation

```python
async def generate_multilingual():
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            "http://localhost:8000/generate",
            params={
                "theme": "friendship adventure",
                "num_pages": 4,
                "languages": ["en", "es"],  # Generate in both English and Spanish
                "style": "3D_RENDERED",
                "pod_ready": True
            }
        )
        job_id = response.json()["job_id"]
        
        # Wait for completion...
        # Files will be available at:
        # - output/{job_id}/storybook_en.pdf
        # - output/{job_id}/storybook_es.pdf
```

### Using Test Scripts

#### Full Integration Test (Real APIs)

```bash
python tests/test_final_product.py
```

Generates a complete 2-page storybook with authenticated APIs. 
- **Duration**: ~3-5 minutes
- **Requires**: Valid API keys in `.env`
- **Output**: PDF in `output/` directory

#### Quick Mock Test (No API Calls)

```bash
python tests/test_quick_demo.py
```

Fast test using mock providers for pipeline validation.
- **Duration**: ~4 seconds
- **Requires**: No API keys
- **Use Case**: Development and CI/CD testing

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py -v

# Run tests with coverage report
pytest --cov=src --cov=services --cov-report=html

# Run only unit tests
pytest tests/test_agents.py tests/test_image_service.py

# Run only integration tests
pytest tests/test_final_product.py tests/test_quick_demo.py
```

### Test Structure

#### Integration Tests

- **`tests/test_final_product.py`**: Complete end-to-end test with real API providers
  - Full storybook generation workflow
  - Real LLM and image generation
  - PDF validation

- **`tests/test_quick_demo.py`**: Quick integration test with mock providers
  - Validates pipeline logic
  - No external API calls
  - Fast execution for CI/CD

#### Unit Tests

- **`tests/test_api.py`**: FastAPI endpoint testing
  - Request/response validation
  - Error handling
  - Status codes

- **`tests/test_agents.py`**: Author and Art Director agent tests
  - Story generation logic
  - Prompt generation
  - Output validation

- **`tests/test_character_service.py`**: Character consistency tests
  - Character extraction
  - Reference generation
  - Visual DNA tracking

- **`tests/test_image_service.py`**: Image generation service tests
  - Provider integration
  - Error handling
  - Format validation

- **`tests/test_llm_client.py`**: LLM client tests
  - Provider switching
  - Fallback logic
  - Timeout handling

- **`tests/test_pdf_generator.py`**: PDF generation tests
  - Layout calculations
  - Page structure
  - File output

- **`tests/test_background_remover.py`**: Image processing tests
  - Background removal
  - Auto-cropping
  - Transparency handling

- **`tests/test_sticker_generator.py`**: Sticker processing tests
  - Format conversion
  - Border application
  - Optimization

### Test Configuration

See `pytest.ini` for test configuration:
- Test discovery patterns
- Async mode configuration
- Output formatting

---

## 🏗️ Project Structure

```
story_booker_v0.1/
├── src/                          # Application source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application & API routes
│   └── models.py                 # Pydantic data models
│
├── services/                     # Core business logic services
│   ├── __init__.py
│   ├── llm_client.py            # Multi-provider LLM client
│   ├── author_agent.py          # Story generation agent
│   ├── art_director_agent.py    # Image prompt generation agent
│   ├── character_service.py     # Character consistency system
│   ├── image_service.py         # Multi-provider image generation
│   ├── background_remover.py    # Background removal & processing
│   ├── sticker_generator.py     # Sticker processing pipeline
│   ├── pdf_generator.py         # PDF layout & generation engine
│   ├── pod_preflight.py         # Print-on-Demand preflight system
│   ├── image_storage.py         # Image file management
│   └── pdf_storage.py           # PDF file management
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_api.py              # API endpoint tests
│   ├── test_agents.py           # Agent service tests
│   ├── test_character_service.py # Character service tests
│   ├── test_image_service.py    # Image service tests
│   ├── test_llm_client.py       # LLM client tests
│   ├── test_pdf_generator.py    # PDF generator tests
│   ├── test_background_remover.py # Background remover tests
│   ├── test_sticker_generator.py # Sticker generator tests
│   ├── test_final_product.py    # End-to-end integration test
│   ├── test_quick_demo.py       # Quick mock integration test
│   ├── TEST_COMMANDS.md         # Test command reference
│   ├── TEST_RESULTS_SUMMARY.md  # Test results documentation
│   └── test_pod_verification.py # POD preflight tests
│
├── assets/                       # Generated images (gitignored)
│   └── {job_id}/                # Job-specific asset directories
│
├── output/                       # Generated PDFs (gitignored)
│   └── {job_id}/                # Job-specific PDF outputs
│
├── .gitignore                   # Git ignore patterns
├── .env                         # Environment variables (not in git)
├── env.example                  # Environment variable template
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
├── plan.txt                     # Development roadmap
├── README.md                    # This file
└── LICENSE                      # MIT License
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### API Key Errors

**❌ "POLLINATIONS_API_KEY is required"**
- Ensure `.env` file exists in project root
- Verify `POLLINATIONS_API_KEY` is set and not a placeholder
- Check for typos or extra spaces around the key
- Restart the server after changing `.env`
- Get your API key at: https://enter.pollinations.ai

**❌ Authentication Failed (401)**
- Verify API keys are valid and not expired
- Check for extra spaces or newlines in `.env` file
- Ensure no quotes around API key values unless necessary
- Regenerate API keys if expired
- Restart server after updating keys

**❌ Rate Limit Exceeded (429)**
- Wait a few minutes before retrying
- Check your API usage limits/quota on provider dashboard
- Use mock provider for testing: `USE_MOCK_PROVIDER=true` in `.env`
- Consider upgrading API tier if frequently hitting limits

#### Timeout Errors

**❌ Timeout Errors**
- Increase timeout values in `.env`:
  - `LLM_TIMEOUT=180` (default: 120)
  - `IMAGE_TIMEOUT=240` (default: 180)
- Check network connectivity and stability
- Verify API provider status pages
- Use faster provider (Groq) for LLM calls

#### PDF Generation Issues

**❌ PDF Not Generated**
- Check job status: `GET /status/{job_id}`
- Verify job status is `"completed"` (not `"failed"`)
- Check `error_message` field in status response
- Review server logs for detailed error information
- Ensure sufficient disk space in `output/` directory

**❌ Job Status Remains "processing"**
- Check server logs for stuck processes
- Verify all API providers are responding
- Check for network connectivity issues
- Restart server if job appears hung

#### Model & Provider Issues

**❌ Model Not Found (Groq)**
- Ensure you're using current model name
- Default: `llama-3.3-70b-versatile`
- Check [Groq documentation](https://console.groq.com/docs/models) for available models
- Update `GROQ_MODEL` in `.env` if needed

**❌ Provider Fallback Not Working**
- Verify fallback providers are configured in `.env`
- Check that fallback provider API keys are valid
- Review error logs for provider-specific issues
- Ensure timeout values allow for fallback execution

#### Image Processing Issues

**❌ Images Not Generating**
- Verify `POLLINATIONS_API_KEY` is valid
- Check image timeout settings
- Verify image provider is operational
- Check network connectivity
- Review `IMAGE_PROVIDER` setting in `.env`

**❌ Poor Image Quality**
- Try different art style (e.g., `3D_RENDERED`, `CLAYMATION`)
- Ensure sufficient image generation timeout
- Check character reference images are generating correctly
- Verify image size settings in prompts

---

## 🌟 Supported Providers

### LLM Providers

| Provider | Speed | Quality | Cost | Use Case | Status |
|----------|-------|---------|------|----------|--------|
| **Groq** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Free tier | Fast inference, recommended default | ✅ Recommended |
| **OpenAI** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Paid (per token) | High-quality, premium results | ✅ Fallback |
| **GPT4All** | ⚡⚡ | ⭐⭐⭐ | Free (local) | Privacy-sensitive, offline use | ✅ Offline option |
| **Mock** | ⚡⚡⚡⚡⚡ | N/A | Free | Testing only | ✅ Testing only |

### Image Providers

| Provider | Quality | Speed | API Key | Use Case | Status |
|----------|---------|-------|---------|----------|--------|
| **Pollinations.ai** | ⭐⭐⭐⭐ | ⚡⚡⚡ | ✅ Required | Default, good quality-price ratio | ✅ Default |
| **OpenAI DALL-E** | ⭐⭐⭐⭐⭐ | ⚡⚡ | ✅ Required | Premium quality, paid | ✅ Optional |
| **Mock** | N/A | ⚡⚡⚡⚡⚡ | ❌ None | Testing only | ✅ Testing only |

---

## 📈 Development Roadmap

### Completed Phases

- ✅ **Phase 1**: API Foundation (FastAPI endpoints, job management)
- ✅ **Phase 2**: Narrative & Prompt Agents (Story & image prompt generation)
- ✅ **Phase 3**: Image Service & Processing (Image generation, background removal)
- ✅ **Phase 4**: PDF Layout Engine (Grid layouts, full-page illustrations)
- ✅ **Phase 5**: Integration & Refinement (Error handling, fallbacks, testing)
- ✅ **Phase 6**: Character Consistency System (Visual DNA, reference images)
- ✅ **Phase 7**: POD Preflight (CMYK conversion, bleeds, KDP validation)
- ✅ **Phase 8**: Multi-Language Support (English, Spanish)

### Current Focus

**Local PDF Factory Development**
- CLI interface for automation
- Batch processing capabilities
- Configuration presets system
- Quality reporting

### Future Enhancements

- 🌐 Web UI for storybook creation
- 📋 Configuration preset manager
- ✍️ Writing style templates (Dr. Seuss, Educational, etc.)
- 📐 Additional trim sizes (square, landscape, custom)
- 💾 Storybook library and history management
- 📊 Analytics and usage statistics
- 🔗 API access for developers
- 🌍 Additional language support
- 📱 Mobile app integration
- 🌌 Shared worlds and character libraries (Phase 3 - Much Later)

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! We appreciate your interest in improving Story Booker.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Make your changes** following our development guidelines
4. **Add tests** for new functionality
5. **Ensure all tests pass** (`pytest`)
6. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
7. **Push to the branch** (`git push origin feature/AmazingFeature`)
8. **Open a Pull Request**

### Development Guidelines

- Follow **PEP 8** style guidelines
- Add comprehensive **tests** for new features
- Update **documentation** as needed
- Ensure all **tests pass** before submitting
- Use **descriptive commit messages**
- Keep **PRs focused** on a single feature/fix

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/guillermopickman-spec/story_booker_v0.1/issues)
- **Documentation**: See `tests/TEST_COMMANDS.md` and `tests/TEST_RESULTS_SUMMARY.md` for additional details
- **Plan & Roadmap**: See `plan.txt` for development roadmap

---

## 🙏 Acknowledgments

- **Groq** for providing fast LLM inference infrastructure
- **Pollinations.ai** for accessible image generation capabilities
- **OpenAI** for DALL-E and GPT model APIs
- **FastAPI** team for the excellent async web framework
- **FPDF2** contributors for PDF generation capabilities
- **Pillow** developers for robust image processing

---

<div align="center">

**Made with ❤️ by [guillermopickman-spec](https://github.com/guillermopickman-spec)**

⭐ **Star this repo if you find it useful!**

[Report Bug](https://github.com/guillermopickman-spec/story_booker_v0.1/issues) • [Request Feature](https://github.com/guillermopickman-spec/story_booker_v0.1/issues) • [Documentation](https://github.com/guillermopickman-spec/story_booker_v0.1#readme)

</div>