# backend/app/services/vector_store.py
"""Stores and searches historical bug embeddings in PostgreSQL with pgvector."""

from typing import List, Dict

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db_models import DefectChunk, HistoricalDefect
from app.db_session import get_session
from app.services.chunking import Chunk
from app.services.embeddings import embed_texts, embed_text


def index_chunks(chunks: List[Chunk], batch_size: int = 512) -> int:
    """Embed and upsert chunks into PostgreSQL. Returns the number indexed."""
    if not chunks:
        return 0

    session = get_session()
    total = 0
    try:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            chunk_ids = [f"{c.bug_id}::{c.chunk_type}::{c.chunk_index}" for c in batch]
            existing = dict(
                session.execute(
                    select(DefectChunk.chunk_id, DefectChunk.chunk_text).where(
                        DefectChunk.chunk_id.in_(chunk_ids)
                    )
                ).all()
            )
            pending = [
                chunk
                for chunk in batch
                if existing.get(f"{chunk.bug_id}::{chunk.chunk_type}::{chunk.chunk_index}")
                != chunk.text
            ]
            if not pending:
                total += len(batch)
                continue

            vectors = embed_texts([c.text for c in pending])

            parent_rows = {
                chunk.bug_id: {"bug_id": chunk.bug_id, "source": chunk.source}
                for chunk in pending
            }
            parent_insert = insert(HistoricalDefect.__table__).values(list(parent_rows.values()))
            session.execute(
                parent_insert.on_conflict_do_nothing(index_elements=[HistoricalDefect.__table__.c.bug_id])
            )

            chunk_rows = []
            for chunk, vector in zip(pending, vectors):
                chunk_rows.append(
                    {
                        "chunk_id": f"{chunk.bug_id}::{chunk.chunk_type}::{chunk.chunk_index}",
                        "historical_bug_id": chunk.bug_id,
                        "chunk_type": chunk.chunk_type,
                        "chunk_text": chunk.text,
                        "embedding": vector,
                        "metadata": {
                            "bug_id": chunk.bug_id,
                            "source": chunk.source,
                            "chunk_type": chunk.chunk_type,
                            "chunk_index": chunk.chunk_index,
                        },
                    }
                )
            chunk_insert = insert(DefectChunk.__table__).values(chunk_rows)
            session.execute(
                chunk_insert.on_conflict_do_update(
                    index_elements=[DefectChunk.__table__.c.chunk_id],
                    set_={
                        "historical_bug_id": chunk_insert.excluded.historical_bug_id,
                        "chunk_type": chunk_insert.excluded.chunk_type,
                        "chunk_text": chunk_insert.excluded.chunk_text,
                        "embedding": chunk_insert.excluded.embedding,
                        "metadata": chunk_insert.excluded.metadata,
                    },
                )
            )
            total += len(batch)

            session.commit()
        return total
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _fallback_text_search(query: str, top_k: int = 5) -> List[Dict]:
    """Fallback text search when sentence-transformers or vector embedding is unavailable."""
    import re
    from sqlalchemy import or_

    stop_words = {"the", "and", "for", "with", "this", "that", "from", "when", "error", "null", "none"}
    words = [w.lower() for w in re.findall(r"[a-zA-Z0-9_]{3,}", query) if w.lower() not in stop_words]
    if not words:
        words = [w.lower() for w in re.findall(r"[a-zA-Z0-9_]{2,}", query)]

    session = get_session()
    try:
        if not words:
            rows = session.execute(
                select(DefectChunk, HistoricalDefect)
                .join(HistoricalDefect, HistoricalDefect.bug_id == DefectChunk.historical_bug_id)
                .limit(top_k)
            ).all()
            return [
                {
                    "id": rec.chunk_id,
                    "text": rec.chunk_text,
                    "metadata": rec.chunk_metadata or {},
                    "similarity_score": 0.5,
                    "title": defect.title or "",
                    "component": defect.component or "",
                    "resolution_summary": defect.resolution or "",
                    "historical_status": defect.status or "",
                }
                for rec, defect in rows
            ]

        conditions = [DefectChunk.chunk_text.ilike(f"%{w}%") for w in words[:10]]
        rows = session.execute(
            select(DefectChunk, HistoricalDefect)
            .join(HistoricalDefect, HistoricalDefect.bug_id == DefectChunk.historical_bug_id)
            .where(or_(*conditions))
            .limit(top_k * 4)
        ).all()

        results = []
        for rec, defect in rows:
            text_lower = rec.chunk_text.lower()
            matches_count = sum(1 for w in words if w in text_lower)
            score = min(0.95, round(matches_count / max(len(words), 1), 4))
            results.append((score, rec, defect))

        results.sort(key=lambda x: x[0], reverse=True)

        matches = []
        for score, rec, defect in results[:top_k]:
            matches.append(
                {
                    "id": rec.chunk_id,
                    "text": rec.chunk_text,
                    "metadata": rec.chunk_metadata or {},
                    "similarity_score": score,
                    "title": defect.title or "",
                    "component": defect.component or "",
                    "resolution_summary": defect.resolution or "",
                    "historical_status": defect.status or "",
                }
            )
        return matches
    except Exception as exc:
        print(f"[VectorStore] Fallback text search failed: {exc}")
        return []
    finally:
        session.close()


def search_similar(query: str, top_k: int = 5) -> List[Dict]:
    """Returns the top_k most semantically similar chunks to the query text."""
    try:
        query_vector = embed_text(query)
        session = get_session()
        try:
            distance = DefectChunk.embedding.cosine_distance(query_vector)
            rows = session.execute(
                select(DefectChunk, HistoricalDefect, distance.label("distance"))
                .join(HistoricalDefect, HistoricalDefect.bug_id == DefectChunk.historical_bug_id)
                .where(DefectChunk.embedding.is_not(None))
                .order_by(distance)
                .limit(top_k)
            ).all()

            matches = []
            for record, defect, cosine_distance in rows:
                similarity = max(0.0, 1.0 - float(cosine_distance))
                matches.append(
                    {
                        "id": record.chunk_id,
                        "text": record.chunk_text,
                        "metadata": record.chunk_metadata or {},
                        "similarity_score": round(similarity, 4),
                        "title": defect.title or "",
                        "component": defect.component or "",
                        "resolution_summary": defect.resolution or "",
                        "historical_status": defect.status or "",
                    }
                )
            return matches
        finally:
            session.close()
    except Exception as exc:
        print(f"[VectorStore] Vector search failed ({exc}). Falling back to text search.")
        return _fallback_text_search(query, top_k)


def collection_count() -> int:
    session = get_session()
    try:
        return session.scalar(select(func.count()).select_from(DefectChunk)) or 0
    finally:
        session.close()
