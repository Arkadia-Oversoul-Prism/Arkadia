# Build the canonical N-ATLaS Lab frontend into the same image as FastAPI.
FROM node:20-bookworm-slim AS console-build

WORKDIR /build
COPY web/console/package.json web/console/package.json
COPY web/console/tsconfig.json ./web/console/
COPY web/console/vite.config.ts web/console/vite.config.ts
COPY web/console/index.html web/console/index.html
COPY web/console/src web/console/src

WORKDIR /build/web/console
RUN npm install --no-audit --no-fund
RUN npm run build


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

# Copy all application files.
COPY . /app

# Replace the source-tree console build with the deterministic production build.
COPY --from=console-build /build/web/console/dist /app/web/console/dist

# Runtime folder for JSON
RUN mkdir -p /run

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
