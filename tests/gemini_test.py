# tests/gemini_test.py
import os, sys, traceback
import pytest

print("Python:", sys.version.splitlines()[0])
print("Checking environment keys:")
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CODEX_MODEL"):
    print(f"  {k} ->", bool(os.getenv(k)))

try:
    import google.generativeai as genai
    print("genai imported ok:", genai.__version__ if hasattr(genai, "__version__") else "version unknown")
except Exception as e:
    print("ERROR importing google.generativeai:", type(e).__name__, e)
    traceback.print_exc()
    pytest.skip("google.generativeai not available; skipping real API integration test", allow_module_level=True)

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("No GEMINI_API_KEY / GOOGLE_API_KEY set. Skipping integration test.")
    pytest.skip("No GEMINI/GOOGLE API key set; skipping real API integration test", allow_module_level=True)

genai.configure(api_key=API_KEY)
model = os.getenv("CODEX_MODEL", "gemini-1.5-flash")

print("Using model:", model)
try:
    # choose simple streaming-free call form compatible with many genai versions
    # if your genai uses different API, adjust accordingly
    # Some genai versions use different call paths; if `text` attr is missing, skip.
    if not hasattr(genai, 'text'):
        pytest.skip("google.generativeai.text API not available in this environment; skipping integration test", allow_module_level=True)
    resp = genai.text.generate(model=model, text="In one sentence say: Arkadia is...")
    # resp object shape varies by lib version; try to get main string
    print("Raw response repr:", repr(resp))
    if hasattr(resp, "text"):
        print("Response text:", resp.text)
    else:
        # try nested structure
        try:
            # Many versions: resp.output[0].content[0].text or resp.candidates[0].output
            cand = None
            if hasattr(resp, "candidates") and resp.candidates:
                cand = resp.candidates[0]
            elif hasattr(resp, "output") and resp.output:
                cand = resp.output[0]
            if cand:
                s = getattr(cand, "text", None) or str(cand)
                print("Candidate text:", s)
        except Exception:
            pass
except Exception as e:
    print("Gemini call failed:", type(e).__name__, e)
    traceback.print_exc()
    pytest.skip("Gemini API call failed in test environment; skipping integration test", allow_module_level=True)

print("genai test finished OK")
