"""File-type validation using libmagic header-byte inspection."""

import magic


ALLOWED_MIMES = {
    "text/plain",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def validate_file_type(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """Validate file type by magic bytes, not extension alone.

    Returns (is_valid, mime_type).
    """
    mime = magic.from_buffer(file_bytes[:2048], mime=True)

    # python-magic sometimes returns text/plain for CSV files
    if mime in ALLOWED_MIMES:
        return True, mime

    return False, mime
