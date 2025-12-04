# ========================
# Render-ready Dockerfile
# ========================

# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files into container
COPY . /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Write the service account JSON from the environment variable
# Render secret: GOOGLE_SERVICE_ACCOUNT_JSON
RUN echo "$GOOGLE_SERVICE_ACCOUNT_JSON" > /app/service_account.json

# Ensure arkadia_console.py is executable
RUN chmod +x /app/arkadia_console.py

# Set default environment variables (can be overridden in Render UI)
ENV GEMINI_API_KEY=$GEMINI_API_KEY
ENV ARKADIA_FOLDER_ID=$ARKADIA_FOLDER_ID
ENV GOOGLE_SERVICE_ACCOUNT_JSON_FILE=/app/service_account.json

# Default command to run Arkadia console
CMD ["python", "arkadia_console.py"]
