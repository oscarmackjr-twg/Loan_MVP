# Elastic Beanstalk Docker image for Loan Engine
# Build from repo root: docker build -f deploy/aws/eb/Dockerfile -t <ECR_URI>:latest .

# ---- Frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN sed -i 's/\r$//' package.json package-lock.json 2>/dev/null || true
RUN npm ci
RUN npm config set strict-ssl false && npm install @rollup/rollup-linux-x64-gnu --no-save && npm config set strict-ssl true
COPY frontend/ ./
RUN find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.json" -o -name "*.js" -o -name "*.mjs" -o -name "*.css" -o -name "*.html" -o -name "*.yaml" -o -name "*.yml" \) ! -path "./node_modules/*" -exec sed -i 's/\r$//' {} \; 2>/dev/null || true
ENV VITE_API_URL=
ENV NODE_ENV=production
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ---- Backend ----
FROM python:3.12-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
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
WORKDIR /app
# Health check for EB/ALB (optional; EB can also use HTTP path health checks)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
