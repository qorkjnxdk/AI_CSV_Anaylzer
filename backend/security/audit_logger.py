"""Rotating audit logger that records uploads, queries, and blocked injections.

All sensitive values (filenames, queries) are SHA-256 hashed before logging
so the trail is useful for forensics without exposing raw user data.
"""

import logging
import hashlib
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

_logger = logging.getLogger("audit")
_logger.setLevel(logging.INFO)

_handler = RotatingFileHandler(
    "audit.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
_handler.setFormatter(logging.Formatter("%(message)s"))
_logger.addHandler(_handler)


def _hash(value: str) -> str:
    """Return the first 16 hex chars of the SHA-256 digest of value."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def log_upload(session_id: str, filename: str, row_count: int):
    """Log a file upload event with hashed filename."""
    _logger.info(
        f"[{datetime.now(timezone.utc).isoformat()}] UPLOAD "
        f"session={session_id[:8]} file_hash={_hash(filename)} rows={row_count}"
    )


def log_query(session_id: str, query: str):
    """Log a data query event with hashed query text."""
    _logger.info(
        f"[{datetime.now(timezone.utc).isoformat()}] QUERY "
        f"session={session_id[:8]} query_hash={_hash(query)}"
    )


def log_injection_attempt(session_id: str, query: str, matched: str):
    """Log a blocked prompt injection attempt with the matched pattern."""
    _logger.info(
        f"[{datetime.now(timezone.utc).isoformat()}] INJECTION_BLOCKED "
        f"session={session_id[:8]} query_hash={_hash(query)} matched={matched}"
    )
