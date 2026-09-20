# Margin Map production image: FastAPI serves the React build + /api
# from a single origin, reading the rebuilt read-only SQLite database.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Node.js (for the frontend production build) + SQLite runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend dependencies first (better layer caching).
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Frontend dependencies.
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci

# Repository source. NOTE on build context and data: the six frozen AO
# CSVs (data/processed/phase4c_*.csv) and quality JSONs must be present in
# the build context. They are intentionally NOT committed to Git (release
# scope excludes generated CSVs/DBs), so build this image where the
# analytical pipeline has been run (locally), or supply the AO files to
# the hosted builder by your own explicit action. load_data.py verifies
# every AO CSV against its tracked quality-JSON SHA-256 and fails loudly.
COPY . .

# Production build: React static assets + read-only analytical database.
# load_data.py verifies every AO CSV against its tracked quality-JSON
# SHA-256 before rebuilding marginmap.db; fails loudly on mismatch.
RUN cd frontend && npm run build
RUN python sql/load_data.py
RUN python sql/validate_sql_outputs.py

EXPOSE 8000

# Render (and most hosts) inject $PORT; default to 8000 locally.
# No --reload in production.
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
