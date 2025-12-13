import os
import time
import requests
from .logger import get_logger

LOGGER = get_logger()

# =========================
# CONFIG
# =========================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL = "models/gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
ENDPOINT = f"{BASE_URL}/{MODEL}:generateContent?key={GEMINI_API_KEY}"

TIMEOUT = 120
MAX_RETRIES = 3
RETRY_DELAY = 3


# =========================
# GEMINI 2.5 CALL
# =========================

def gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
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
                ENDPOINT,
                json=payload,
                timeout=TIMEOUT,
            )

            if r.status_code != 200:
                last_error = f"{r.status_code}: {r.text}"
                LOGGER.warning("[Gemini retry %s/%s] %s", attempt, MAX_RETRIES, last_error)
                time.sleep(RETRY_DELAY)
                continue

            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            LOGGER.warning("[Gemini retry %s/%s] %s", attempt, MAX_RETRIES, last_error)
            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"Gemini failed after retries: {last_error}")


# =========================
# PROVIDER REGISTRY (FUTURE)
# =========================

PROVIDERS = {
    "gemini": gemini,
}

def available_providers() -> dict:
    """Return a mapping of provider -> availability boolean."""
    providers = {}
    # For now only gemini has a key to check
    providers["gemini"] = bool(os.environ.get("GEMINI_API_KEY"))
    return providers


def call_llm(provider: str, prompt: str) -> str:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider}")
    return PROVIDERS[provider](prompt)
