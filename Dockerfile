# Build both Arkadia user-facing applications into the canonical Render image.
FROM node:24-bookworm-slim AS frontend-build

WORKDIR /build

# Primary Arkadia experience: Solariun, Arkana, Canvas, and the existing Prism UI.
COPY web/public_prism/ ./web/public_prism/
RUN npm install --global pnpm@10.26.1 \
 && cd web/public_prism \
 && pnpm install --frozen-lockfile \
 && pnpm run build

# Reconciled operator console and focused N-ATLaS tester.
COPY web/console/ ./web/console/
WORKDIR /build/web/console
RUN npm ci --no-audit --no-fund \
 && npm run build


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Baked source revision for the read-only GET /api/version endpoint (ADR-016).
#
# Empty by default, and NOT supplied by any repository build path: the only
# docker build in this repository (.github/workflows/n-atlas-developer-lab.yml,
# job "Build canonical Render image") runs `docker build --pull -t <tag> .`
# with no --build-arg. So this build argument is inert unless a build supplies
# it explicitly; at runtime on Render the reported revision comes from the
# provider-injected RENDER_GIT_COMMIT.
#
# The empty default is also load-bearing: an empty or absent value is classified
# as absent metadata and falls through to the provider commit instead of being
# mistaken for a revision. If a future build does bake a revision here and it
# disagrees with the provider commit, GET /api/version reports
# revision_conflict: true rather than silently preferring the baked value.
ARG ARKADIA_SOURCE_REVISION=""
ENV ARKADIA_SOURCE_REVISION=${ARKADIA_SOURCE_REVISION}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    wget \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY . /app

# Replace source-tree output with the deterministic builds from the frontend stage.
COPY --from=frontend-build /build/web/public_prism/dist /app/web/public_prism/dist
COPY --from=frontend-build /build/web/console/dist /app/web/console/dist

RUN mkdir -p /run
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
