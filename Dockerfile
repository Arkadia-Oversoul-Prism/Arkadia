# Build the one Arkadia application into the canonical Render image.
#
# The canonical shell is the Arkadia Console (web/arkadia_console). It builds ONE
# bundle that serves the product at the origin root *and* the operator surface at
# /operator and the external N-ATLaS tester at /n-atlas-lab — those are routes of
# this application, not mounts of a second one.
#
# Two frontends are deliberately NOT built:
#   * the retired Prism UI, archived under archive/frontend/arkadia-prism;
#   * the former standalone operator application (web/console), whose capabilities
#     were migrated into web/arkadia_console's route hierarchy. Its source is
#     retained for a reversible retirement, but it is no longer part of the image.
FROM node:24-bookworm-slim AS frontend-build

WORKDIR /build

# The one application: shell, Arkana, Solariun, Engineering Lab, SolSpire,
# Knowledge OS, Weaver, About, the Operator surface and the N-ATLaS tester.
#
# The retired Prism UI is archived under archive/frontend/arkadia-prism and is
# intentionally NOT built. See that directory's README for recovery.
COPY web/arkadia_console/ ./web/arkadia_console/
RUN npm install --global pnpm@10.26.1 \
 && cd web/arkadia_console \
 && pnpm install --frozen-lockfile \
 && pnpm run build


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

# Replace source-tree output with the deterministic build from the frontend stage.
COPY --from=frontend-build /build/web/arkadia_console/dist /app/web/arkadia_console/dist

RUN mkdir -p /run
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
