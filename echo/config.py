"""Settings: models, paths, limits.

The OpenRouter key is never stored in the code or the repository. It is read, in this order, from:
the OPENROUTER_API_KEY environment variable, Streamlit secrets (Streamlit Cloud), the local file
~/.secrets/common.env (author's machine).
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
INDEX_DIR = ROOT / "index"
PROMPTS_DIR = ROOT / "prompts"

BASE_URL = "https://openrouter.ai/api/v1"
CHAT_MODEL = os.environ.get("ECHO_CHAT_MODEL", "anthropic/claude-haiku-4.5")
EMBED_MODEL = "openai/text-embedding-3-small"
TEMPERATURE = 0
MAX_TOKENS = 1200
# Haiku 5.5 reasons by default and spends the output budget on it; the answer schema needs no reasoning
EXTRA_BODY = {"reasoning": {"enabled": False}}
CACHE_CONTROL = {"type": "ephemeral", "ttl": "1h"}  # Anthropic prompt cache via OpenRouter

TOP_K = 4               # fact fragments found by meaning (templates excluded)
TEMPLATE_SLOTS = 2      # extra fragments from the reply templates (doc 01)
ALWAYS_ON = ("04", "07", "08", "09")  # defect procedure, classification, routing, special cases: whole, every request
NOT_INDEXED = ("10",)  # weekly summary examples: the summary is out of the MVP

MAX_INPUT_CHARS = 1500
MAX_REQUESTS_PER_SESSION = 15


def secret(name: str) -> str | None:
    if value := os.environ.get(name):
        return value
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets.toml: Streamlit raises instead of returning empty
        pass
    env_file = Path.home() / ".secrets" / "common.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == name and value.strip():
                return value.strip().strip("'\"")
    return None


def api_key() -> str:
    if key := secret("OPENROUTER_API_KEY"):
        return key
    raise RuntimeError("Нет ключа OPENROUTER_API_KEY: задайте переменную окружения или Streamlit secrets")


def repo_url() -> str | None:
    """Base URL of the kb/ folder on GitHub, e.g. https://github.com/<user>/echo-assistant/blob/main"""
    url = secret("REPO_URL")
    return url.rstrip("/") if url else None
