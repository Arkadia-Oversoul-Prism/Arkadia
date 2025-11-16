# Lightweight Arkana Oracle API (no Rasa, FastAPI only)

FROM python:3.11-slim

WORKDIR /app

# Install system deps (sometimes needed for pip builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy app files
COPY arkana_app.py requirements.txt ./

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) copy corpora if arkana_app will read them
COPY arkana_rasa/ arkana_rasa/
COPY Oversoul_Prism/ Oversoul_Prism/

ENV PORT=8000
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "arkana_app:app", "--host", "0.0.0.0", "--port", "8000"]
