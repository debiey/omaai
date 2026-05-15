"""
OmaAI Configuration Manager
Loads from ~/.omaai/config.yaml
Switch provider: oma config --set provider ollama
"""

import os
import yaml
from pathlib import Path
from typing import Optional

CONFIG_DIR  = Path.home() / ".omaai"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "provider": "ollama",
    "model": {
        "ollama":    "gemma3:1b",
        "openai":    "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
    },
    "ollama_host":      "http://localhost:11434",
    "max_tokens":       1500,
    "temperature":      0.3,
    "safe_mode":        True,
    "dry_run_default":  True,
    "monitor_interval": 3,
}


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE) as f:
        loaded = yaml.safe_load(f) or {}
    # Always merge with defaults so new keys are never missing
    merged = DEFAULT_CONFIG.copy()
    merged.update(loaded)
    return merged


def save_config(cfg: dict):
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def get_api_key(provider: str) -> Optional[str]:
    """Read API key from environment variable."""
    env_map = {
        "openai":    "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_var = env_map.get(provider)
    if env_var:
        return os.environ.get(env_var)
    return None  # Ollama needs no key
