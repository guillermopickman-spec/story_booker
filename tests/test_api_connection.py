"""
Quick test to check if LLM API is working and not rate-limited.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(override=True)

from services.llm_client import get_llm_client


async def test_api_connection():
    """Test if the configured LLM API is working."""
    print("="*80)
    print("API CONNECTION TEST")
    print("="*80)
    print()
    
    # Get configuration
    provider = os.getenv("LLM_PROVIDER", "groq")
    timeout = float(os.getenv("LLM_TIMEOUT", "120"))
    
    print(f"Provider: {provider}")
    print(f"Timeout: {timeout}s")
    print()
    
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        placeholder_values = ["your_groq_api_key_here", "your_api_key_here", ""]
        if not api_key or api_key.lower() in [p.lower() for p in placeholder_values]:
            print("[ERROR] GROQ_API_KEY is not set or is a placeholder!")
            return False
        print("[OK] GROQ_API_KEY is set")
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        placeholder_values = ["your_openai_api_key_here", "your_api_key_here", ""]
        if not api_key or api_key.lower() in [p.lower() for p in placeholder_values]:
            print("[ERROR] OPENAI_API_KEY is not set or is a placeholder!")
            return False
        print("[OK] OPENAI_API_KEY is set")
    
    print()
    print("Testing API connection...")
    print("-" * 80)
    
    try:
        llm_client = get_llm_client(provider=provider)
        
        test_messages = [
            {"role": "user", "content": "Say 'API test successful' and nothing else."}
        ]
        
        print(f"Sending test request to {provider}...")
        start_time = asyncio.get_event_loop().time()
        
        response = await llm_client.generate(
            messages=test_messages,
            temperature=0.7,
            use_fallback=False
        )
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"[OK] Response received in {elapsed:.2f}s")
        print(f"Response: {response[:100]}..." if len(response) > 100 else f"Response: {response}")
        print()
        print("="*80)
        print("[SUCCESS] API CONNECTION TEST PASSED!")
        print("="*80)
        return True
        
    except asyncio.TimeoutError as e:
        print()
        print("="*80)
        print("[ERROR] API TEST FAILED: TIMEOUT")
        print("="*80)
        print(f"Error: {str(e)}")
        print()
        print("Possible causes:")
        print("- Network connectivity issues")
        print("- API server is slow or unresponsive")
        print("- Timeout setting too low")
        return False
        
    except Exception as e:
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        print()
        print("="*80)
        
        rate_limit_indicators = [
            "rate limit", "429", "quota", "limit exceeded", 
            "too many requests", "throttled"
        ]
        is_rate_limit = any(indicator in error_str for indicator in rate_limit_indicators)
        
        if is_rate_limit or "429" in error_str:
            print("[ERROR] API TEST FAILED: RATE LIMIT EXCEEDED")
            print("="*80)
            print(f"Error: {str(e)}")
            print()
            print("[WARNING] You have hit the API rate limit!")
            print()
            print("Solutions:")
            print("1. Wait a few minutes and try again")
            print("2. Check your API usage limits:")
            if provider == "groq":
                print("   - Groq Console: https://console.groq.com/usage")
            elif provider == "openai":
                print("   - OpenAI Usage: https://platform.openai.com/usage")
            print("3. Use a different provider (set LLM_PROVIDER in .env)")
            print("4. Use mock provider for testing (set USE_MOCK_PROVIDER=true)")
        else:
            print("[ERROR] API TEST FAILED")
            print("="*80)
            print(f"Error Type: {error_type}")
            print(f"Error: {str(e)}")
            print()
            print("Possible causes:")
            print("- Invalid API key")
            print("- Network connectivity issues")
            print("- API service is down")
            if provider == "groq":
                print("- Check Groq status: https://status.groq.com/")
            elif provider == "openai":
                print("- Check OpenAI status: https://status.openai.com/")
        
        print()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_api_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
