"""In-memory session store with automatic TTL-based expiration."""

import uuid
import time
from typing import Any

SESSION_TTL_SECONDS = 3600  # 60 minutes

_sessions: dict[str, dict[str, Any]] = {}


def create_session() -> str:
    """Create a new session with empty file, history, and feedback stores. Returns the session ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "created_at": time.time(),
        "last_accessed": time.time(),
        "files": {},       # {filename: {sheet_name: DataFrame}}
        "history": [],     # list of prompt history entries
        "feedback": {},    # {prompt_index: "up" | "down"}
    }
    return session_id


def get_session(session_id: str) -> dict[str, Any] | None:
    """Retrieve a session by ID, returning None if expired or missing."""
    session = _sessions.get(session_id)
    if session is None:
        return None
    if time.time() - session["last_accessed"] > SESSION_TTL_SECONDS:
        del _sessions[session_id]
        return None
    session["last_accessed"] = time.time()
    return session


def cleanup_expired_sessions():
    """Remove all sessions that have exceeded the TTL. Called periodically by the app lifespan."""
    now = time.time()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s["last_accessed"] > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _sessions[sid]
