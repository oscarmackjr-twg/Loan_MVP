# Multi-stage: build frontend, then backend + static files
# Build from repo root: docker build -f deploy/Dockerfile .

# ---- Frontend ---- (Debian base avoids Alpine musl + npm optional-deps/SSL issues)
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
# Normalize CRLF to LF when building from Windows
RUN sed -i 's/\r$//' package.json package-lock.json 2>/dev/null || true
RUN npm ci
# Lockfile from Windows omits linux Rollup binary (npm optional-deps bug). Install it; relax SSL only for this fetch if behind corporate proxy.
RUN npm config set strict-ssl false && npm install @rollup/rollup-linux-x64-gnu --no-save && npm config set strict-ssl true
COPY frontend/ ./
RUN find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.json" -o -name "*.js" -o -name "*.mjs" -o -name "*.css" -o -name "*.html" -o -name "*.yaml" -o -name "*.yml" \) ! -path "./node_modules/*" -exec sed -i 's/\r$//' {} \; 2>/dev/null || true
# Point API to same origin in production (backend serves both)
ENV VITE_API_URL=
ENV NODE_ENV=production
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ---- Backend ----
FROM python:3.12-slim AS backend
WORKDIR /app
# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
# Trust PyPI hosts if build is behind SSL-inspecting proxy (e.g. corporate)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org \
        -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/dist ./static
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
# Run from backend dir so api.main resolves
WORKDIR /app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
