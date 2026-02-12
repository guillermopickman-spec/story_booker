# Story Booker - Windows Setup Guide

This guide explains how to set up and run Story Booker on Windows.

## Prerequisites

1. **Python 3.8+** - Make sure Python is installed and added to your PATH
2. **Docker Desktop for Windows** - Required to run ComfyUI
3. **Node.js 16+** - Required for the frontend
4. **Git** - For cloning the repository

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/story-booker.git
cd story-booker
```

### 2. Set Up Environment Variables

Copy the environment template and modify it as needed:

```bash
copy .env.example .env
```

Edit `.env` file with your settings. The default configuration should work for most setups:

```
# ComfyUI Connection Settings
# Note: Leave COMFYUI_HOST empty to use auto-discovery (recommended)
COMFYUI_HOST=
COMFYUI_PORT=8188
COMFYUI_TIMEOUT=10
COMFYUI_MAX_RETRIES=3
COMFYUI_RETRY_DELAY=2

# ComfyUI Prompt Configuration
CHARACTER_WORKFLOW_NAME="character_creator"
POSITIVE_PROMPT="high quality, masterpiece, detailed, 8k"
NEGATIVE_PROMPT="low quality, blurry, distorted, text, watermark"
USE_NEGATIVE_PROMPT=false

# Environment Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd apps/frontend
npm install
cd ../..
```

### 5. Start ComfyUI with Docker

Use Docker Compose to start ComfyUI:

```bash
docker-compose up -d
```

This will:
- Pull the ComfyUI image
- Start ComfyUI on port 8188
- Mount volumes for workflows and outputs
- Set up automatic restart

Check that ComfyUI is running by visiting http://localhost:8188 in your browser.

### 6. Run the Backend

```bash
cd apps/backend
python main.py
```

The backend API will start on http://localhost:8000 by default.

### 7. Run the Frontend

In a new terminal:

```bash
cd apps/frontend
npm run dev
```

The frontend will start on http://localhost:3000.

## Project Structure

```
story-booker/
├── apps/
│   ├── backend/          # FastAPI backend service
│   └── frontend/         # Next.js frontend app
├── modules/
│   ├── characters/       # Character generation modules
│   └── shared_utils/     # Shared utilities
├── workflows/            # ComfyUI workflow files
├── tests/               # Test files
├── docker-compose.yml    # Docker configuration
└── .env.example         # Environment variables template
```

## Troubleshooting

### ComfyUI Connection Issues

1. **Verify ComfyUI is running**
   ```bash
   docker ps | grep comfyui
   ```

2. **Check ComfyUI logs**
   ```bash
   docker logs comfyui
   ```

3. **Test connection manually**
   ```bash
   curl http://localhost:8188
   ```

### Port Conflicts

If port 8188 is already in use, modify the `docker-compose.yml` file to use a different port:

```yaml
ports:
  - "8189:8188"  # Change host port to 8189
```

Then update your `.env` file:
```
COMFYUI_PORT=8189
```

### Windows-Specific Issues

1. **WSL Gateway Detection**
   The client now includes Windows-specific host detection that should work without WSL.

2. **File Paths**
   The workflow composer has been updated to handle Windows paths, including the default ComfyUI installation path.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Adding New Workflows

1. Place your workflow JSON files in the `workflows/` directory
2. The system will automatically detect and use them
3. Or specify a custom workflow name in your `.env` file:
   ```
   CHARACTER_WORKFLOW_NAME="my_custom_workflow"
   ```

## API Endpoints

### Backend API

- `GET /` - Basic status message
- `GET /health` - Health check endpoint

Future endpoints will be documented here as they are added.

### ComfyUI Integration

The application integrates with ComfyUI through the following endpoints:

- `POST /prompt` - Queue a generation job
- `GET /history/{prompt_id}` - Check job status
- `GET /queue` - Get current queue status

## Contributing

When contributing to this project:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Test on Windows before submitting

## License

[Your license information here]