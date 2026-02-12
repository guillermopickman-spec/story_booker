# Story Booker Setup Instructions

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- npm or yarn for Node.js
- pip for Python

## Quick Setup

### 1. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd apps/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

### 2. Backend Setup

#### Option 1: Using the Simple Test Backend (Recommended for quick testing)

1. Navigate to the project root directory:
   ```bash
   cd /path/to/Story_Booker
   ```

2. Start the simple test backend:
   ```bash
   python -m apps.backend.simple_test
   ```

3. The backend will be available at `http://localhost:8000`

#### Option 2: Using the Full Backend (Requires ComfyUI and Ollama)

1. Make sure ComfyUI is running and accessible (can be installed locally or via other means)
2. Make sure Ollama is installed and running
3. Configure your `.env` file with the appropriate settings
4. Navigate to the project root directory:
   ```bash
   cd /path/to/Story_Booker
   ```

5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Start the backend:
   ```bash
   python -m apps.backend.main
   ```

## Environment Variables

The following environment variables can be configured in your `.env` file:

### ComfyUI Configuration
- `COMFYUI_HOST`: ComfyUI host (default: empty for auto-discovery)
- `COMFYUI_PORT`: ComfyUI port (default: 8188)
- `COMFYUI_TIMEOUT`: Connection timeout in seconds (default: 10)
- `COMFYUI_MAX_RETRIES`: Maximum connection retries (default: 3)
- `COMFYUI_RETRY_DELAY`: Delay between retries in seconds (default: 2)

### ComfyUI Prompt Configuration
- `CHARACTER_WORKFLOW_NAME`: Name of the workflow to use (default: "character_creator")
- `POSITIVE_PROMPT`: Default positive prompt (default: "high quality, masterpiece, detailed, 8k")
- `NEGATIVE_PROMPT`: Default negative prompt (default: "low quality, blurry, distorted, text, watermark")
- `USE_NEGATIVE_PROMPT`: Whether to use negative prompt (default: false)

### Ollama Configuration
- `OLLAMA_HOST`: Ollama host (default: 127.0.0.1)
- `OLLAMA_PORT`: Ollama port (default: 11434)
- `OLLAMA_MODEL`: Ollama model to use (default: "llama3.1:8b")
- `OLLAMA_TIMEOUT`: Connection timeout in seconds (default: 30)
- `OLLAMA_MAX_RETRIES`: Maximum connection retries (default: 3)

### Description Generation Settings
- `DESCRIPTION_STYLE`: Style for generated descriptions (default: "detailed, evocative, suitable for image generation")
- `DESCRIPTION_TEMPERATURE`: Temperature for generation (default: 0.7)
- `DESCRIPTION_MAX_TOKENS`: Maximum tokens for generation (default: 512)

### General Settings
- `ENVIRONMENT`: Environment (development/production) (default: development)
- `LOG_LEVEL`: Logging level (default: INFO)

## Project Structure

```
Story_Booker/
├── apps/
│   ├── frontend/          # Next.js frontend
│   └── backend/          # FastAPI backend
├── modules/              # Core modules
│   ├── characters/       # Character generation modules
│   └── shared_utils/     # Shared utilities
├── requirements.txt      # Python dependencies
├── apps/frontend/requirements.txt  # Frontend dependencies
└── .env                 # Environment variables
```

## API Endpoints

### Test Backend Endpoints

- `GET /` - Basic API information
- `GET /health` - Health check
- `POST /generate-image` - Generate image (test mode)
- `POST /generate-description` - Generate description (test mode)
- `POST /generate-image-with-description` - Generate both (test mode)

### Full Backend Endpoints

- `GET /` - Basic API information
- `GET /health` - Health check
- `POST /generate-image` - Generate image using ComfyUI
- `POST /generate-description` - Generate description using Ollama
- `POST /generate-image-with-description` - Generate both

## Running Without Docker

This project no longer requires Docker. The application can be run directly with:

1. **Frontend** (Next.js):
   ```bash
   cd apps/frontend && npm run dev
   ```

2. **Backend** (FastAPI):
   ```bash
   # For testing (no external dependencies)
   python -m apps.backend.simple_test
   
   # For full functionality (requires ComfyUI and Ollama)
   python -m apps.backend.main
   ```

## Troubleshooting

### Frontend Issues

1. Make sure Node.js is installed and up to date
2. Clear the npm cache: `npm cache clean --force`
3. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### Backend Issues

1. Make sure Python is installed and up to date
2. Install dependencies: `pip install -r requirements.txt`
3. For the full backend, ensure ComfyUI and Ollama are running
4. Check the `.env` file configuration

### CORS Issues

If you encounter CORS errors, make sure:
1. The frontend is running on `http://localhost:3000`
2. The backend is configured to allow origins from `http://localhost:3000`

## Testing

Run the test suite:

```bash
# Python backend tests
python -m pytest tests/

# Frontend tests (if implemented)
cd apps/frontend && npm test
```

## Installation Notes

- Docker has been removed as a dependency
- The application now runs directly on your machine
- ComfyUI and Ollama are optional dependencies for full functionality
- The simple test backend works without external dependencies