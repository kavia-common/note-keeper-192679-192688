# Notes Backend (FastAPI)

A minimal FastAPI backend that exposes CRUD endpoints for managing notes.

## Features
- Health check: GET /health
- Notes CRUD:
  - GET /notes
  - GET /notes/{id}
  - POST /notes
  - PUT /notes/{id}
  - DELETE /notes/{id}
- Pydantic models: NoteCreate, NoteUpdate, NoteRead
- CORS enabled for local development
- In-memory repository (can be swapped for a DB later)
- OpenAPI docs at /docs

## Requirements
- Python 3.10+
- pip

## Setup
```bash
cd notes_backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run
Using uvicorn:
```bash
export PORT=3001  # optional, defaults to 3001
uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-3001}
```

Alternatively, run the module directly:
```bash
python src/api/main.py
```

Then open:
- API Docs: http://localhost:3001/docs
- Health: http://localhost:3001/health

## Configuration
Environment variables (see .env.example):
- PORT: Port for the server (default: 3001)
- CORS_ALLOW_ORIGINS: Comma-separated origins; default "*" for development
- NOTES_USE_INT_IDS: "true" to use integer IDs; default uses UUIDs

## Notes
This service uses an in-memory repository for simplicity. Data resets on restart. To persist data, replace `InMemoryRepository` with a database-backed implementation.
