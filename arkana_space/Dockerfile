# Dockerfile for Arkana of Arkadia — HuggingFace Temple (Docker SDK)

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HuggingFace Spaces usually binds to PORT=7860 by convention
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
