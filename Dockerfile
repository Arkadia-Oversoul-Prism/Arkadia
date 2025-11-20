FROM python:3.11-slim

# Work directory inside the container
WORKDIR /app

# System deps (for compiling some Python wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Arkadia repo into the container
# This brings in:
# - arkana_app.py
# - brain.py
# - db.py
# - models.py
# - memory_engine.py
# - queue_engine.py
# - arkadia_drive_sync.py
# - arkadia_corpus_map.json
# - 50_Code_Modules, Oversoul_Prism, arkana_rasa, etc.
COPY . .

# Render will usually inject PORT; default to 8000 if not set
ENV PORT=8000

EXPOSE 8000

# Start the Oracle Temple
CMD ["sh", "-c", "uvicorn arkana_app:app --host 0.0.0.0 --port ${PORT}"]
