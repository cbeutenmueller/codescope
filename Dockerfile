# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build/codescope/frontend

# Copy both package.json and package-lock.json (if present).
# Once you have a lockfile committed, change `npm install` → `npm ci` for
# reproducible, tamper-evident installs.
COPY codescope/frontend/package*.json ./
RUN npm install --ignore-scripts

COPY codescope/frontend/ ./
# vite.config.ts resolves outDir to ../server/static relative to __dirname
RUN npm run build


# ── Stage 2: Build Python environment ─────────────────────────────────────────
FROM python:3.13-slim AS python-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install third-party dependencies before copying source (better layer caching).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source then inject the built frontend assets.
COPY codescope/ ./codescope/
COPY --from=frontend-builder /build/codescope/server/static/ ./codescope/server/static/

# Install the project itself (creates the codescope entry-point in the venv).
RUN uv sync --frozen --no-dev


# ── Stage 3: Runtime ───────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Dedicated non-root user — no login shell, no password.
RUN groupadd -g 10000 codescope \
    && useradd -u 10000 -g 10000 -M -s /sbin/nologin codescope

WORKDIR /app

# Venv + app source (editable install references /app/codescope at runtime).
COPY --from=python-builder --chown=10000:10000 /app/.venv  /app/.venv
COPY --from=python-builder --chown=10000:10000 /app/codescope /app/codescope

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER 10000:10000

# Mount the project to review here.
VOLUME /workspace
WORKDIR /workspace

EXPOSE 8421

ENTRYPOINT ["codescope"]
CMD ["--help"]
