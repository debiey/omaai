"""
OmaAI AI Engine
Unified interface for Ollama, OpenAI, and Anthropic.
Switch anytime: oma config --set provider ollama
"""

from abc import ABC, abstractmethod
from oma.config import load_config, get_api_key


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        pass


class OllamaProvider(LLMProvider):
    def __init__(self, cfg: dict):
        self.host        = cfg.get("ollama_host", "http://localhost:11434")
        self.model       = cfg["model"]["ollama"]
        self.max_tokens  = cfg["max_tokens"]
        self.temperature = cfg["temperature"]

    def complete(self, system: str, user: str) -> str:
        import httpx
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        try:
            timeout = httpx.Timeout(
                connect=10.0,
                read=600.0,
                write=30.0,
                pool=10.0,
            )
            r = httpx.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except httpx.ConnectError:
            raise SystemExit(
                f"❌  Cannot reach Ollama at {self.host}\n"
                "    Run:  ollama serve"
            )


class OpenAIProvider(LLMProvider):
    def __init__(self, cfg: dict):
        try:
            from openai import OpenAI
        except ImportError:
            raise SystemExit("❌  Run: pip install openai")
        key = get_api_key("openai")
        if not key:
            raise SystemExit(
                "❌  OPENAI_API_KEY not set.\n"
                "    export OPENAI_API_KEY=sk-..."
            )
        self.client      = OpenAI(api_key=key)
        self.model       = cfg["model"]["openai"]
        self.max_tokens  = cfg["max_tokens"]
        self.temperature = cfg["temperature"]

    def complete(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()


class AnthropicProvider(LLMProvider):
    def __init__(self, cfg: dict):
        try:
            import anthropic
        except ImportError:
            raise SystemExit("❌  Run: pip install anthropic")
        key = get_api_key("anthropic")
        if not key:
            raise SystemExit(
                "❌  ANTHROPIC_API_KEY not set.\n"
                "    export ANTHROPIC_API_KEY=sk-ant-..."
            )
        self.client     = anthropic.Anthropic(api_key=key)
        self.model      = cfg["model"]["anthropic"]
        self.max_tokens = cfg["max_tokens"]

    def complete(self, system: str, user: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text.strip()


PROVIDERS = {
    "ollama":    OllamaProvider,
    "openai":    OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_engine() -> LLMProvider:
    cfg      = load_config()
    provider = cfg.get("provider", "ollama").lower()
    if provider not in PROVIDERS:
        raise SystemExit(
            f"❌  Unknown provider '{provider}'.\n"
            f"    Valid options: {', '.join(PROVIDERS.keys())}\n"
            "    Fix: oma config --set provider ollama"
        )
    return PROVIDERS[provider](cfg)


def list_providers() -> dict:
    return {
        "ollama":    "Free · runs locally · no API key · default",
        "openai":    "Paid · fast · needs OPENAI_API_KEY",
        "anthropic": "Paid · strong reasoning · needs ANTHROPIC_API_KEY",
    }
