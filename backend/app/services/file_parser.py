# backend/app/services/file_parser.py
"""Turns an uploaded file into plain text the rest of the pipeline can use."""

import json
from pathlib import Path

from app.config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES


class UnsupportedFileError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


def validate_upload(filename: str, size_bytes: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise UnsupportedFileError(f"'{ext}' is not supported. Allowed types: {allowed}")
    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise FileTooLargeError(f"File is larger than the {max_mb:.0f}MB limit.")


def extract_text(filename: str, raw_bytes: bytes) -> str:
    """Returns the file's content as plain text, regardless of .txt/.log/.json."""
    ext = Path(filename).suffix.lower()
    decoded = raw_bytes.decode("utf-8", errors="replace")

    if ext == ".json":
        try:
            parsed = json.loads(decoded)
            # Pretty-print so nested stack traces/log objects stay readable downstream.
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            # Not actually valid JSON despite the extension — fall back to raw text
            # rather than rejecting the upload outright.
            return decoded

    return decoded
