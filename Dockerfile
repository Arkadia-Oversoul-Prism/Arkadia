FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    wget \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . /app

# Runtime folder for JSON
RUN mkdir -p /run

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
