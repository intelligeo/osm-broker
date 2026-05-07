FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Dipendenze Python (stesse del backend + duckdb)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il monorepo (il worker accede a resources/ e backend/app/)
COPY . .

ENV PYTHONPATH=/app/backend

CMD ["python", "worker/worker.py"]
