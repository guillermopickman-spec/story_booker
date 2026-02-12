Image Generation Module
This sub-module handles the connection to ComfyUI, workflow assembly, and the final generation of character-related images.

📂 Module Structure
1. client.py
Location: modules/characters/image_gen/client.py

The core engine for communicating with the ComfyUI backend.

Connectivity: Automatically finds the server and performs health checks to ensure the connection is active.

Execution: Feeds the finalized JSON workflows to the ComfyUI API.

Retrieval: Listens for execution completion and receives the generated image data.

Status Tracking (Planned): Integration for real-time progress checking during long-render tasks.

2. workflow_composer.py
Location: modules/characters/image_gen/workflow_composer.py

Responsible for building the instructions sent to the generator.

Workflow Management: Retrieves saved .json workflows from the /workflows directory based on the name specified in your environment variables.

Prompt Injection: Dynamically injects the POSITIVE_PROMPT and NEGATIVE_PROMPT from your .env configuration.

Conditional Logic: Only includes the negative prompt if it is explicitly enabled/set to true in your environment.

API Sync (Planned): Ability to pull live workflows directly from a running ComfyUI instance.

⚙️ Environment Variables Required
To use these modules, ensure the following are set in your .env file:

COMFY_SERVER_ADDRESS: The URL/IP of your ComfyUI instance.

ACTIVE_WORKFLOW_NAME: The filename of the workflow to load from /workflows.

POSITIVE_PROMPT: The default text to guide image generation.

ENABLE_NEGATIVE_PROMPT: Boolean (true/false) to toggle negative prompt injection.