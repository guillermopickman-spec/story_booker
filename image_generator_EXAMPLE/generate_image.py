#!/usr/bin/env python3
"""
Pollinations.ai Image Generation Script

Generates AI images using the Pollinations API.
Get your API key at: https://enter.pollinations.ai
"""

import requests
import argparse
import os
import sys
from urllib.parse import quote
from datetime import datetime


def generate_image(prompt, api_key, model="flux", output_file=None):
    """
    Generate an AI image using Pollinations API.
    
    Args:
        prompt (str): The image generation prompt
        api_key (str): Your Pollinations API key
        model (str): The model to use (default: 'flux')
        output_file (str): Optional output filename. If not provided, generates one.
    
    Returns:
        str: Path to the saved image file
    """
    # URL encode the prompt
    encoded_prompt = quote(prompt)
    
    # Construct the API URL
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model={model}"
    
    # Set up headers with API key
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"Generating image with model '{model}'...")
    print(f"Prompt: {prompt}")
    print("Please wait...")
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Determine output filename
        if output_file is None:
            # Create a safe filename from the prompt
            safe_prompt = "".join(c for c in prompt[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{safe_prompt}_{timestamp}.png"
        
        # Ensure output directory exists (if path includes directory)
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Save the image
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"[OK] Image saved successfully: {output_file}")
        return output_file
        
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error: {e}", file=sys.stderr)
        if response.status_code == 401:
            print("  Authentication failed. Please check your API key.", file=sys.stderr)
        elif response.status_code == 404:
            print("  Model not found. Check available models with --list-models", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}", file=sys.stderr)
        sys.exit(1)


def list_models(api_key, model_type="image"):
    """
    List available models from the Pollinations API.
    
    Args:
        api_key (str): Your Pollinations API key
        model_type (str): Type of models to list ('image' or 'text')
    """
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    if model_type == "image":
        url = "https://gen.pollinations.ai/image/models"
    else:
        url = "https://gen.pollinations.ai/v1/models"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        models = response.json()
        
        print(f"\nAvailable {model_type} models:")
        print("-" * 50)
        if isinstance(models, list):
            for model in models:
                if isinstance(model, dict) and 'id' in model:
                    print(f"  - {model['id']}")
                else:
                    print(f"  - {model}")
        elif isinstance(models, dict):
            for key, value in models.items():
                print(f"  - {key}: {value}")
        else:
            print(models)
            
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI images using Pollinations API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_image.py "a cat playing piano" --api-key YOUR_KEY
  python generate_image.py "sunset over mountains" --model flux --api-key YOUR_KEY --output sunset.png
  python generate_image.py --list-models --api-key YOUR_KEY

Get your API key at: https://enter.pollinations.ai
        """
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The image generation prompt"
    )
    
    parser.add_argument(
        "--api-key",
        help="Your Pollinations API key (or set POLLINATIONS_API_KEY env var)",
        default=os.getenv("POLLINATIONS_API_KEY", "sk_beXxNv3vBFLJ0CqecWfDMIeqDOjCIfzO")
    )
    
    parser.add_argument(
        "--model",
        default="flux",
        help="The model to use (default: flux)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output filename for the generated image"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available image models"
    )
    
    parser.add_argument(
        "--list-text-models",
        action="store_true",
        help="List available text models"
    )
    
    args = parser.parse_args()
    
    # Check if API key is provided
    if not args.api_key:
        print("Error: API key is required.", file=sys.stderr)
        print("Set it with --api-key or POLLINATIONS_API_KEY environment variable.", file=sys.stderr)
        print("Get your API key at: https://enter.pollinations.ai", file=sys.stderr)
        sys.exit(1)
    
    # List models if requested
    if args.list_models:
        list_models(args.api_key, "image")
        return
    
    if args.list_text_models:
        list_models(args.api_key, "text")
        return
    
    # Check if prompt is provided
    if not args.prompt:
        parser.print_help()
        sys.exit(1)
    
    # Generate the image
    generate_image(args.prompt, args.api_key, args.model, args.output)


if __name__ == "__main__":
    main()
