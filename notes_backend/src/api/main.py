import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_TITLE = "Notes Backend API"
APP_DESC = (
    "A simple Notes API with CRUD operations. "
    "Provides endpoints to create, read, update, and delete notes."
)
APP_VERSION = "0.1.0"

# PUBLIC_INTERFACE
class NoteBase(BaseModel):
    """Base schema shared across Note models."""
    title: str = Field(..., description="Title of the note", min_length=1, max_length=500)
    content: str = Field(..., description="Content/body of the note", min_length=0)

# PUBLIC_INTERFACE
class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass

# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    title: Optional[str] = Field(None, description="Updated title of the note", min_length=1, max_length=500)
    content: Optional[str] = Field(None, description="Updated content/body of the note", min_length=0)

# PUBLIC_INTERFACE
class NoteRead(NoteBase):
    """Schema for reading a note."""
    id: Union[int, uuid.UUID] = Field(..., description="Unique identifier of the note")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")

# Simple in-memory persistence; could be swapped for SQLite/DB later.
class InMemoryRepository:
    """A minimal in-memory repository for Notes. Uses UUID identifiers by default."""
    def __init__(self, use_int_ids: bool = False) -> None:
        self._use_int_ids = use_int_ids
        self._store: Dict[Union[int, uuid.UUID], NoteRead] = {}
        self._next_id = 1

    def _gen_id(self) -> Union[int, uuid.UUID]:
        if self._use_int_ids:
            nid = self._next_id
            self._next_id += 1
            return nid
        return uuid.uuid4()

    # PUBLIC_INTERFACE
    def list_notes(self) -> List[NoteRead]:
        """Return all notes."""
        return list(self._store.values())

    # PUBLIC_INTERFACE
    def get_note(self, note_id: Union[int, uuid.UUID]) -> Optional[NoteRead]:
        """Get a note by id."""
        return self._store.get(note_id)

    # PUBLIC_INTERFACE
    def create_note(self, data: NoteCreate) -> NoteRead:
        """Create a new note."""
        now = datetime.utcnow()
        nid = self._gen_id()
        note = NoteRead(id=nid, title=data.title, content=data.content, created_at=now, updated_at=now)
        self._store[nid] = note
        return note

    # PUBLIC_INTERFACE
    def update_note(self, note_id: Union[int, uuid.UUID], data: NoteUpdate) -> Optional[NoteRead]:
        """Update an existing note."""
        current = self._store.get(note_id)
        if not current:
            return None
        updated = current.model_copy(
            update={
                "title": data.title if data.title is not None else current.title,
                "content": data.content if data.content is not None else current.content,
                "updated_at": datetime.utcnow(),
            }
        )
        self._store[note_id] = updated
        return updated

    # PUBLIC_INTERFACE
    def delete_note(self, note_id: Union[int, uuid.UUID]) -> bool:
        """Delete a note by id. Returns True if deleted."""
        return self._store.pop(note_id, None) is not None


def _bool_env(var_name: str, default: bool = False) -> bool:
    val = os.getenv(var_name)
    if val is None:
        return default
    return str(val).lower() in {"1", "true", "yes", "y", "on"}

# Configure repository: default to UUID identifiers; allow int ids via env for compatibility.
USE_INT_IDS = _bool_env("NOTES_USE_INT_IDS", False)
repo = InMemoryRepository(use_int_ids=USE_INT_IDS)

openapi_tags = [
    {
        "name": "Health",
        "description": "Health and diagnostics endpoints",
    },
    {
        "name": "Notes",
        "description": "Operations with notes (CRUD)",
    },
]

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESC,
    version=APP_VERSION,
    openapi_tags=openapi_tags,
)

# CORS for local dev (can be restricted via ENV)
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.get(
    "/health",
    summary="Health Check",
    description="Returns service health status.",
    tags=["Health"],
    responses={200: {"description": "Service is healthy"}},
)
def health_check():
    """Health check endpoint returning a simple status."""
    return {"status": "ok"}

def _parse_id(id_str: str) -> Union[int, uuid.UUID]:
    """Parse path id according to repository id type."""
    if USE_INT_IDS:
        try:
            return int(id_str)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid integer ID")
    try:
        return uuid.UUID(id_str)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid UUID")

# PUBLIC_INTERFACE
@app.get(
    "/notes",
    summary="List Notes",
    description="Retrieve all notes.",
    tags=["Notes"],
    response_model=List[NoteRead],
    responses={200: {"description": "List of notes"}},
)
def list_notes() -> List[NoteRead]:
    """List all notes currently stored."""
    return repo.list_notes()

# PUBLIC_INTERFACE
@app.get(
    "/notes/{id}",
    summary="Get Note",
    description="Retrieve a single note by its ID.",
    tags=["Notes"],
    response_model=NoteRead,
    responses={404: {"description": "Note not found"}},
)
def get_note(
    id: str = Path(..., description="Note identifier (int or UUID based on configuration)")
) -> NoteRead:
    """Get a note by ID."""
    nid = _parse_id(id)
    note = repo.get_note(nid)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# PUBLIC_INTERFACE
@app.post(
    "/notes",
    summary="Create Note",
    description="Create a new note.",
    tags=["Notes"],
    response_model=NoteRead,
    status_code=201,
)
def create_note(payload: NoteCreate) -> NoteRead:
    """Create a new note and return it."""
    return repo.create_note(payload)

# PUBLIC_INTERFACE
@app.put(
    "/notes/{id}",
    summary="Update Note",
    description="Update a note by its ID.",
    tags=["Notes"],
    response_model=NoteRead,
    responses={404: {"description": "Note not found"}},
)
def update_note(
    payload: NoteUpdate,
    id: str = Path(..., description="Note identifier (int or UUID based on configuration)"),
) -> NoteRead:
    """Update an existing note."""
    nid = _parse_id(id)
    updated = repo.update_note(nid, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated

# PUBLIC_INTERFACE
@app.delete(
    "/notes/{id}",
    summary="Delete Note",
    description="Delete a note by its ID.",
    tags=["Notes"],
    responses={
        204: {"description": "Note deleted"},
        404: {"description": "Note not found"},
    },
    status_code=204,
)
def delete_note(
    id: str = Path(..., description="Note identifier (int or UUID based on configuration)")
):
    """Delete a note by ID."""
    nid = _parse_id(id)
    deleted = repo.delete_note(nid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return None


# Convenience: enable `python -m uvicorn` or `python src/api/main.py`
if __name__ == "__main__":
    import uvicorn

    # Respect PORT env var if provided; default to 3001 as required by preview system
    port = int(os.getenv("PORT", "3001"))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=False)
