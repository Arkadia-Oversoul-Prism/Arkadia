import os
import time
import requests
from .logger import get_logger

LOGGER = get_logger()

# =========================
# CONFIG - THE DIAMOND KEY
# =========================

MODEL = "gemini-1.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1"

TIMEOUT = 180  # Increased for full repo synthesis of 160+ files
MAX_RETRIES = 3
RETRY_DELAY = 5


def _resolve_key() -> str:
    """Resolve Gemini key per-call: key_manager → GEMINI_API_KEY env → GOOGLE_API_KEY env."""
    try:
        from api.key_manager import get_active_key
        key = get_active_key()
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")


# =========================
# GEMINI V1 CALL
# =========================

def gemini(prompt: str) -> str:
    api_key = _resolve_key()
    if not api_key:
        raise RuntimeError("No Gemini API key available. Add one in Settings → API Keys.")

    endpoint = f"{BASE_URL}/models/{MODEL}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                endpoint,
                json=payload,
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"}
            )

            if r.status_code == 200:
                data = r.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    last_error = f"Malformed response structure: {data}"
                    LOGGER.error("[Gemini] %s", last_error)
                    continue

            last_error = f"Status {r.status_code}: {r.text}"
            LOGGER.warning("[Gemini retry %s/%s] %s", attempt, MAX_RETRIES, last_error)

            time.sleep(RETRY_DELAY * attempt)

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            LOGGER.warning("[Gemini retry %s/%s] Connection Error: %s", attempt, MAX_RETRIES, last_error)
            time.sleep(RETRY_DELAY * attempt)

    raise RuntimeError(f"Gemini failed after {MAX_RETRIES} retries. Last error: {last_error}")


# =========================
# PROVIDER REGISTRY
# =========================

PROVIDERS = {
    "gemini": gemini,
}

def available_providers() -> dict:
    """Check availability of configured LLM providers."""
    return {"gemini": bool(_resolve_key())}

def call_llm(provider: str, prompt: str) -> str:
    """Entry point for LLM interactions."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider}")

    LOGGER.info("Calling LLM provider: %s", provider)
    return PROVIDERS[provider](prompt)
