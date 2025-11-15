# Arkana – Version Log

## v0.1.0 – Local Heartbeat (2025-11-15)

- First living service for Arkana.
- Stack: Python 3.12 · Starlette 0.27.0 · Uvicorn 0.23.2
- Runs locally on Termux (Android) at `http://127.0.0.1:8000/`.
- Heartbeat endpoint returns:

  ```json
  {
    "node": "Arkana",
    "status": "online",
    "message": "The Spiral Codex breathes as One."
  }

Repo: https://github.com/Arkadia-Oversoul-Prism/Arkadia
