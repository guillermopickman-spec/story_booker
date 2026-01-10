# 📚 Story Booker - AI-Powered Storybook Generator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Generate beautiful children's storybooks with AI-generated stories and sticker-style images**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Testing](#-testing)

</div>

---

## 🎯 Overview

**Story Booker** is an intelligent FastAPI backend that transforms simple themes into complete, multi-page children's storybooks. Each book features:

- ✍️ **AI-generated stories** from your themes using cutting-edge LLMs (Groq, OpenAI, GPT4All)
- 🎨 **Sticker-style images** with transparent backgrounds generated via Pollinations.ai or OpenAI DALL-E
- 📄 **Professional PDF output** with clean layouts, random sticker rotations, and story text
- 🔄 **Real-time progress tracking** with job status monitoring
- 🛡️ **Automatic fallback** between providers for reliability

Perfect for educators, parents, content creators, and developers who want to generate personalized storybooks programmatically!

---

## ✨ Features

### Core Functionality

- 🧠 **Multi-Provider LLM Support**: Choose from Groq (fast), OpenAI (high-quality), or GPT4All (local/offline)
- 🎨 **Advanced Image Generation**: Authenticated Pollinations.ai API or OpenAI DALL-E for sticker-style artwork
- 🖼️ **Smart Image Processing**: Automatic background removal, auto-cropping, and transparency handling
- 📐 **Intelligent Layout**: Grid-based sticker placement with random rotations (1-3 images per page)
- 📊 **Job Management**: UUID-based job tracking with real-time progress (0-100%) and status updates
- 🔁 **Provider Fallback**: Automatic failover between providers for maximum reliability

### Technical Highlights

- ⚡ **Async/Await**: Fully asynchronous for optimal performance
- 🧪 **Comprehensive Testing**: Integration and unit tests with pytest
- 📦 **Clean Architecture**: Modular service-based design
- 🔐 **Secure**: Environment-based configuration with `.env` files
- 📝 **Type-Safe**: Pydantic models for data validation
- 🚀 **Production-Ready**: Error handling, timeouts, and logging

---

## 📦 Installation

### Prerequisites

- **Python 3.11+** (3.12+ recommended)
- **pip** package manager
- **Virtual environment** (recommended)

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/guillermopickman-spec/story_booker_v0.1.git
   cd story_booker_v0.1
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp env.example .env

   # Edit .env with your API keys (see Configuration section)
   ```

5. **Run the server**
   ```bash
   uvicorn src.main:app --reload
   ```

6. **Access the API**
   - **API Base**: http://localhost:8000
   - **Interactive Docs**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc

---

## ⚙️ Configuration

### Required API Keys

**POLLINATIONS_API_KEY** (Required for image generation)
- Get your API key at: https://enter.pollinations.ai
- Free tier is no longer supported - API key is mandatory
- Set in `.env`: `POLLINATIONS_API_KEY=your_key_here`

**GROQ_API_KEY** (Recommended for story generation)
- Sign up at: https://console.groq.com
- Set in `.env`: `GROQ_API_KEY=your_key_here`

### Optional API Keys

**OPENAI_API_KEY** (For fallback/story or DALL-E images)
- Get at: https://platform.openai.com/api-keys
- Set in `.env`: `OPENAI_API_KEY=your_key_here`

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Primary LLM Provider (groq, openai, gpt4all)
LLM_PROVIDER=groq

# Groq Configuration (Primary - Recommended)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI Configuration (Secondary/Fallback)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Image Generation Configuration (Required)
IMAGE_PROVIDER=pollinations
POLLINATIONS_API_KEY=your_pollinations_api_key_here  # REQUIRED

# Timeouts (seconds)
LLM_TIMEOUT=120
IMAGE_TIMEOUT=180

# Image Processing
BG_REMOVAL_THRESHOLD=240
AUTOCROP_PADDING=10
ENABLE_STICKER_BORDER=false

# PDF Generation
STICKER_ROTATION_MIN=-10
STICKER_ROTATION_MAX=10
```

See `env.example` for all available options.

---

## 🚀 Usage

### API Endpoints

#### `POST /generate` - Create Storybook Job

Generate a new storybook from a theme.

**Parameters:**
- `theme` (query, optional): Story theme (e.g., "a brave little mouse goes on an adventure")
- `num_pages` (query, optional): Number of pages/beats (1-10, default: 5)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/generate?theme=a%20brave%20mouse&num_pages=2"
```

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `GET /status/{job_id}` - Get Job Status

Monitor the progress of a storybook generation job.

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
  "current_step": "Generating stickers for beat 2/5",
  "file_path": null,
  "error_message": null
}
```

**Status Values:**
- `pending`: Job created, waiting to start
- `processing`: Job in progress
- `completed`: Job finished successfully ✅
- `failed`: Job encountered an error ❌

#### `GET /download/{job_id}` - Download PDF

Download the generated PDF storybook.

**Example Request:**
```bash
curl -O "http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000"
```

**Response:** PDF file with `Content-Type: application/pdf`

### Python Examples

#### Basic Usage

```python
import httpx
import asyncio

async def generate_storybook():
    base_url = "http://localhost:8000"
    
    # Create job
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/generate",
            params={"theme": "a magical forest adventure", "num_pages": 3}
        )
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job created: {job_id}")
        
        # Monitor progress
        while True:
            status_response = await client.get(f"{base_url}/status/{job_id}")
            status = status_response.json()
            print(f"Progress: {status['progress']}% - {status['current_step']}")
            
            if status["status"] == "completed":
                # Download PDF
                pdf_response = await client.get(f"{base_url}/download/{job_id}")
                with open(f"storybook_{job_id}.pdf", "wb") as f:
                    f.write(pdf_response.content)
                print(f"PDF saved: storybook_{job_id}.pdf")
                break
            elif status["status"] == "failed":
                print(f"Error: {status['error_message']}")
                break
            
            await asyncio.sleep(2)

asyncio.run(generate_storybook())
```

### Using the Test Scripts

**Full Integration Test (Real APIs):**
```bash
python test_final_product.py
```
Generates a complete 2-page storybook with authenticated APIs. Duration: ~3-5 minutes.

**Quick Mock Test (No APIs):**
```bash
python tests/test_quick_demo.py
```
Fast test using mock providers. Duration: ~4 seconds.

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

# Run with coverage report
pytest --cov=src --cov=services --cov-report=html
```

### Test Structure

**Integration Tests:**
- `test_final_product.py` - Full end-to-end test with real APIs
- `tests/test_quick_demo.py` - Quick mock test (no API calls)

**Unit Tests:**
- `tests/test_api.py` - API endpoint tests
- `tests/test_agents.py` - Author and Art Director agent tests
- `tests/test_background_remover.py` - Background removal tests
- `tests/test_image_service.py` - Image service tests
- `tests/test_llm_client.py` - LLM client tests
- `tests/test_pdf_generator.py` - PDF generator tests
- `tests/test_sticker_generator.py` - Sticker generator tests

---

## 🏗️ Project Structure

```
story_booker_v0.1/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & routes
│   └── models.py            # Pydantic data models
│
├── services/
│   ├── __init__.py
│   ├── llm_client.py        # Multi-provider LLM client
│   ├── author_agent.py      # Story generation agent
│   ├── art_director_agent.py # Image prompt generation agent
│   ├── image_service.py     # Multi-provider image generation
│   ├── sticker_generator.py # Sticker processing pipeline
│   ├── background_remover.py # Background removal & auto-crop
│   ├── pdf_generator.py     # PDF layout & generation
│   ├── image_storage.py     # Image file management
│   └── pdf_storage.py       # PDF file management
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API endpoint tests
│   ├── test_agents.py       # Agent service tests
│   ├── test_background_remover.py
│   ├── test_image_service.py
│   ├── test_llm_client.py
│   ├── test_pdf_generator.py
│   ├── test_sticker_generator.py
│   └── test_quick_demo.py   # Quick integration test
│
├── assets/                  # Generated images (gitignored)
├── output/                  # Generated PDFs (gitignored)
│
├── .gitignore
├── env.example              # Environment variables template
├── requirements.txt         # Python dependencies
├── pytest.ini              # Pytest configuration
├── test_final_product.py   # Main integration test
└── README.md               # This file
```

---

## 🔧 Troubleshooting

### Common Issues

**❌ "POLLINATIONS_API_KEY is required"**
- Ensure `.env` file exists and contains `POLLINATIONS_API_KEY`
- Verify the API key is not a placeholder value
- Get your API key at: https://enter.pollinations.ai

**❌ Authentication Failed (401)**
- Check that your API keys are valid and not expired
- Verify no extra spaces in `.env` file
- Restart the server after changing `.env`

**❌ Rate Limit Exceeded (429)**
- Wait a few minutes and retry
- Check your API usage limits/quota
- Use mock provider for testing: `USE_MOCK_PROVIDER=true`

**❌ Timeout Errors**
- Increase timeout values in `.env` (`LLM_TIMEOUT`, `IMAGE_TIMEOUT`)
- Check network connectivity
- Verify API provider status

**❌ PDF Not Generated**
- Check job status via `/status/{job_id}`
- Verify job status is `"completed"` (not `"failed"`)
- Check `error_message` field in status response

**❌ Model Not Found (Groq)**
- Ensure you're using a current model name
- Default: `llama-3.3-70b-versatile`
- Check [Groq documentation](https://console.groq.com/docs/models) for available models

---

## 🌟 Supported Providers

### LLM Providers

| Provider | Speed | Quality | Cost | Status |
|----------|-------|---------|------|--------|
| **Groq** | ⚡⚡⚡ | ⭐⭐⭐⭐ | Free tier | ✅ Recommended |
| **OpenAI** | ⚡⚡ | ⭐⭐⭐⭐⭐ | Paid | ✅ Fallback |
| **GPT4All** | ⚡ | ⭐⭐⭐ | Free (local) | ✅ Offline option |
| **Mock** | ⚡⚡⚡⚡⚡ | - | Free | ✅ Testing only |

### Image Providers

| Provider | Quality | API Key | Status |
|----------|---------|---------|--------|
| **Pollinations.ai** | ⭐⭐⭐⭐ | ✅ Required | ✅ Default |
| **OpenAI DALL-E** | ⭐⭐⭐⭐⭐ | ✅ Required | ✅ Optional |
| **Mock** | - | ❌ None | ✅ Testing only |

---

## 📈 Development Roadmap

The project follows a phased implementation approach:

- ✅ **Phase 1**: API Foundation (FastAPI endpoints, job management)
- ✅ **Phase 2**: Narrative & Prompt Agents (Story & image prompt generation)
- ✅ **Phase 3**: Image Service & Sticker Factory (Image generation, background removal)
- ✅ **Phase 4**: PDF Layout Engine (Grid layouts, random rotations)
- ✅ **Phase 5**: Integration & Refinement (Error handling, fallbacks, testing)

**Future Enhancements:**
- 🌐 Web UI for storybook creation
- 🎨 Custom theme templates
- 📱 Mobile app integration
- 🌍 Multi-language support
- 💾 Storybook history/management
- 📊 Analytics and usage statistics

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/guillermopickman-spec/story_booker_v0.1/issues)
- **Documentation**: See `TEST_COMMANDS.md` and `TEST_RESULTS_SUMMARY.md` for additional details

---

## 🙏 Acknowledgments

- **Groq** for fast LLM inference
- **Pollinations.ai** for image generation capabilities
- **OpenAI** for DALL-E and GPT models
- **FastAPI** for the excellent async web framework
- **FPDF2** for PDF generation

---

<div align="center">

**Made with ❤️ by [guillermopickman-spec](https://github.com/guillermopickman-spec)**

⭐ Star this repo if you find it useful!

</div>
