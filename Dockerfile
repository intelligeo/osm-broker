# ── Stage 1: build frontend ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_URL=/api
ARG VITE_AUTH_ENABLED=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED
RUN npm run build

# ── Stage 2: API + static serving ────────────────────────────────────────
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Installa dipendenze Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copia monorepo (accesso a resources/qstyles_swissmap e backend/app)
COPY . .

# Copia frontend buildato
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

ENV PYTHONPATH=/app/backend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
