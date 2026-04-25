"""OmaAI - Ollama AI engine"""

import httpx
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "tinyllama"


def ask(prompt: str, max_tokens: int = 400) -> str:
    """Send a prompt to Ollama and return the response."""
    try:
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3,
                },
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except httpx.ConnectError:
        return "❌ Cannot connect to Ollama. Is it running? Try: ollama serve"
    except httpx.TimeoutException:
        return "❌ Ollama timed out. Try a smaller model or restart Ollama."
    except Exception as e:
        return f"❌ Error: {e}"
