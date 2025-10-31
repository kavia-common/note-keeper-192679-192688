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
- Notes search:
  - GET /notes/search?q=term&limit=20&offset=0
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

## Endpoint: Search Notes
- Method: GET
- Path: /notes/search
- Query Parameters:
  - q (string, required): Case-insensitive substring to search in title or content.
  - limit (int, optional, default 20): Max number of results (0-100).
  - offset (int, optional, default 0): Number of results to skip.
- Behavior:
  - Returns notes matching q in title or content.
  - Ordered by updated_at descending.
  - Paginated per limit and offset.
- Response: 200 OK with JSON array of NoteRead.
- Errors:
  - 422 Validation Error if q missing/empty or params invalid.

### Example Requests
```bash
# Basic search
curl "http://localhost:3001/notes/search?q=meeting"

# With pagination
curl "http://localhost:3001/notes/search?q=todo&limit=10&offset=20"
```

### Example Response
```json
[
  {
    "id": "b0c3a9d6-9d8c-4a6e-9a1e-3d0b8a0c9f1a",
    "title": "Meeting notes",
    "content": "Discussed Q3 roadmap",
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-02T08:30:00Z"
  }
]
```

## Configuration
Environment variables (see .env.example):
- PORT: Port for the server (default: 3001)
- CORS_ALLOW_ORIGINS: Comma-separated origins; default "*" for development
- NOTES_USE_INT_IDS: "true" to use integer IDs; default uses UUIDs

## Notes
This service uses an in-memory repository for simplicity. Data resets on restart. To persist data, replace `InMemoryRepository` with a database-backed implementation.
