# backend/app/services/chunking.py
"""
Chunking strategy for the Historical Defect Knowledge Base (M1.4).

Design decision: chunk by FIELD first (description, stack_trace, comments,
resolution), not by blindly splitting the whole bug report as one blob.
Reasons:
  - A stack trace and a prose description have very different structure —
    mixing them in one chunk dilutes the embedding for both.
  - At retrieval time we usually want to know WHICH part matched (e.g. "the
    stack trace is similar" vs "the fix description is similar"), so keeping
    that as chunk metadata is more useful for the agents that use this later.
  - Long fields (a big stack trace, a long comment thread) still get split
    further with overlap, so no single embedding has to represent too much
    text at once (embedding quality drops on very long inputs).
"""

from dataclasses import dataclass
from typing import List

from app.config import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS

# These are the fields we chunk independently for every historical bug report.
CHUNKABLE_FIELDS = ["description", "stack_trace", "comments", "resolution"]

# Bare status words with no other context are useless as retrieval results —
# e.g. a resolution field containing only "INVALID" or "FIXED". Skip chunks
# that are just one of these on their own.
_LOW_INFO_VALUES = {"fixed", "invalid", "wontfix", "worksforme", "duplicate", "incomplete", "unresolved", "open"}


@dataclass
class Chunk:
    bug_id: str
    source: str          # 'mozilla' | 'apache' | 'eclipse'
    chunk_type: str       # which field this chunk came from
    chunk_index: int      # position within that field, if it was split further
    text: str


def _split_long_text(text: str, size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """Splits long text into overlapping windows, breaking on whitespace where possible."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # Try not to cut a word in half — walk back to the last space.
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # ensures forward progress
    return chunks


def chunk_bug_report(bug_row: dict) -> List[Chunk]:
    """
    bug_row is one cleaned historical bug record with keys:
      bug_id, source, description, stack_trace, comments, resolution
    Returns a flat list of Chunk objects ready for embedding.
    """
    chunks: List[Chunk] = []
    for field in CHUNKABLE_FIELDS:
        raw_text = (bug_row.get(field) or "").strip()
        if not raw_text or raw_text.lower() in _LOW_INFO_VALUES:
            continue
        for i, piece in enumerate(_split_long_text(raw_text)):
            chunks.append(
                Chunk(
                    bug_id=bug_row["bug_id"],
                    source=bug_row.get("source", "unknown"),
                    chunk_type=field,
                    chunk_index=i,
                    text=piece,
                )
            )
    return chunks
