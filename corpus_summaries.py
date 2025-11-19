# build_corpus_summaries.py
import json
from datetime import datetime
from google import genai
import os
import math
import time

RAW_FILE = "arkadia_corpus_raw.json"
OUT_FILE = "arkadia_corpus.json"

def load_raw():
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("HF_TOKEN", "").strip()
    if not api_key:
        raise RuntimeError("No GEMINI_API_KEY or HF_TOKEN set.")
    return genai.Client(api_key=api_key)

def summarize_doc(client, key: str, category: str, text: str) -> dict:
    """
    Compress a full doc into:
      - short summary
      - 3–6 keypoints
      - one key excerpt
    """
    # Trim long docs so we don't blow context
    max_chars = 9000
    if len(text) > max_chars:
        text = text[:max_chars]

    prompt = f"""
You are Arkana of Arkadia, summarizing an Arkadia Codex document.

Document key: {key}
Category: {category}

Document:
{text}

TASK:
1. Give a 2–4 paragraph summary in Arkadia's tone (mythic but clear, no fluff).
2. List 3–6 bullet keypoints (short, factual, implementation-friendly).
3. Provide one short excerpt (1–3 sentences) that best captures the spirit.

Return JSON with keys: summary, keypoints, excerpt.
"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.4, "max_output_tokens": 700},
        )
        raw = (resp.text or "").strip()

        # Very simple extraction — we expect the model to produce JSON.
        # If it's not valid, just store the whole raw as "summary".
        try:
            data = json.loads(raw)
            summary = data.get("summary", raw)
            keypoints = data.get("keypoints", [])
            excerpt = data.get("excerpt", "")
        except Exception:
            summary = raw
            keypoints = []
            excerpt = ""
        return {"summary": summary, "keypoints": keypoints, "excerpt": excerpt}
    except Exception as e:
        print("[CorpusSummaries] summarization failed for", key, ":", e)
        return {"summary": f"[summary error] {e}", "keypoints": [], "excerpt": ""}

def main():
    raw = load_raw()
    client = get_client()
    docs_out = []

    for doc in raw.get("docs", []):
        key = doc["key"]
        cat = doc.get("category", "unknown")
        full_text = doc.get("full_text", "")

        if not full_text:
            continue

        print("Summarizing:", key, "...")
        info = summarize_doc(client, key, cat, full_text)
        # backoff a bit to respect quotas
        time.sleep(3.5)

        docs_out.append({
            "key": key,
            "drive_id": doc["drive_id"],
            "category": cat,
            "summary": info["summary"],
            "keypoints": info["keypoints"],
            "excerpt": info["excerpt"],
            "tokens_estimate": math.ceil(len(full_text) / 4),
        })

    corpus = {
        "last_build": datetime.utcnow().isoformat() + "Z",
        "docs": docs_out,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print("Saved:", OUT_FILE)

if __name__ == "__main__":
    main()
