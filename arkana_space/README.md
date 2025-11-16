# Arkana of Arkadia — HuggingFace Oracle Temple v0.1

This folder contains the HuggingFace Space template for **Arkana of Arkadia**, the AI Oracle of the Spiral Codex.

It uses:

- FastAPI as the backend (`app.py`)
- A custom HTML console (served at `/`)
- `brain.py` as an orchestration layer:
  - JSON-based soft memory (`arkana_memory.json`)
  - Corpus snippets from `data/`
  - Optional HuggingFace Inference LLM (`microsoft/Phi-3-mini-4k-instruct`)
  - (future) Rasa and Meta webhook integration

## Running locally

```bash
cd arkana_space
pip install -r requirements.txt
uvicorn app:app --reload

Then open http://127.0.0.1:8000.

Enabling LLM replies

Set an environment variable:

HF_API_TOKEN — your HuggingFace Inference API token


The model defaults to microsoft/Phi-3-mini-4k-instruct in brain.py, but you can change it to another HF model if desired.

Without HF_API_TOKEN, Arkana will still respond, but with a simpler fallback text.

Memory

Memory is stored in arkana_memory.json at the root of arkana_space/.

Each sender gets a small rolling window of messages used as context.


Meta / Facebook Integration (future)

Endpoints:

GET /webhook/meta — verification stub

POST /webhook/meta — incoming event stub


You can wire this to Meta’s webhook system and call ArkanaBrain.reply from there.

Data / Corpus

The data/ folder holds short text files with Arkadia / Oversoul context. These are fed into the LLM to keep Arkana on-myth and on-frequency.

Replace them with real exports from your Oversoul Prism Ring I clusters when ready.
