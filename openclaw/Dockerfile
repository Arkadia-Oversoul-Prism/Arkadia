FROM node:22-slim

# Install build tools for any native npm deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install OpenClaw globally
RUN npm install -g openclaw@latest

WORKDIR /app

# Copy config
COPY config.json .

EXPOSE 3000

CMD ["openclaw", "start", "--config", "config.json"]
