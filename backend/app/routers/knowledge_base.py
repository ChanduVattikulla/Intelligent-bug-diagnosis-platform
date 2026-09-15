# backend/app/routers/knowledge_base.py
"""
Historical Defect Knowledge Base API (M1.4): exposes semantic search over the
indexed Mozilla/Apache/Eclipse bug chunks. This is the RAG "retrieval" half —
there's no LLM call here yet (that's the AI Agent Layer, later milestones).
"""

from fastapi import APIRouter, HTTPException

from app.schemas import KnowledgeBaseSearchRequest, KnowledgeBaseSearchResponse
from app.services import vector_store

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])


@router.post("/search", response_model=KnowledgeBaseSearchResponse)
def search_knowledge_base(payload: KnowledgeBaseSearchRequest):
    if vector_store.collection_count() == 0:
        raise HTTPException(
            status_code=503,
            detail=(
                "The knowledge base is empty. Run "
                "`python scripts/ingest_knowledge_base.py` first to index historical bugs."
            ),
        )

    raw_matches = vector_store.search_similar(payload.query, top_k=payload.top_k)

    matches = [
        {
            "source_bug_id": m["metadata"]["bug_id"],
            "source": m["metadata"]["source"],
            "chunk_type": m["metadata"]["chunk_type"],
            "text": m["text"],
            "similarity_score": m["similarity_score"],
            "metadata": m["metadata"],
        }
        for m in raw_matches
    ]
    return {"query": payload.query, "matches": matches}


@router.get("/status")
def knowledge_base_status():
    return {"indexed_chunk_count": vector_store.collection_count()}
