"""The Gemini text-model fallback ladder.

Every Gemini text call site iterates this ladder so that one unavailable model
degrades to the next instead of failing the whole surface. It lives in
``kernel`` (no httpx/fastapi import) so both ``api`` and ``kernel`` call sites
can import it without a cycle.

This is the only definition. Import it; do not re-declare it.
``tests/test_gemini_model_ladder.py`` enforces that, and enforces that a
site-specific model is expressed as a ladder that includes this one rather
than as a bare literal inside a request URL.
"""

GEMINI_MODELS: tuple[str, ...] = (
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
)
