# Base image with Python
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps needed for some python packages (gcc etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python deps
# Ensure requirements.txt lists google-generativeai, google-api-python-client, google-auth, google-auth-httplib2, google-auth-oauthlib, requests
# If you don't have requirements.txt, we install minimal set here
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir google-generativeai google-api-python-client google-auth requests rich; fi

# Ensure entrypoint is executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port if your app serves HTTP (if not, ignore)
EXPOSE 5005

# Use the entrypoint script to write credentials from env and start the app
ENTRYPOINT ["/app/entrypoint.sh"]
