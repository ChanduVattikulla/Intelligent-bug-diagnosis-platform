# backend/app/routers/knowledge_base.py
"""
Historical Defect Knowledge Base API (M1.4): exposes semantic search over the
indexed Mozilla/Apache/Eclipse bug chunks. This is the RAG "retrieval" half —
there's no LLM call here yet (that's the AI Agent Layer, later milestones).
"""

from fastapi import APIRouter, HTTPException

from app.schemas import KnowledgeBaseSearchRequest, KnowledgeBaseSearchResponse, ResolveSubmissionRequest
from app.services import vector_store
from app.db_session import get_session
from app.db_models import DiagnosisSession, BugSubmission, DefectChunk
from app.services.chunking import Chunk
from sqlalchemy import select
from datetime import datetime

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


@router.post("/resolve")
def resolve_bug(payload: ResolveSubmissionRequest):
    session = get_session()
    try:
        diag = session.get(DiagnosisSession, payload.session_id)
        if not diag:
            raise HTTPException(status_code=404, detail="Session not found")
            
        bug = session.get(BugSubmission, diag.bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail="Bug not found")
            
        # Deduplication check
        existing = session.scalar(
            select(DefectChunk).where(DefectChunk.historical_bug_id == bug.id).limit(1)
        )
        if existing:
            return {"status": "already_indexed", "message": "Bug already in knowledge base"}
            
        chunks = []
        source_name = "bugfix_ai_user"
        
        # 1. Create Resolution Chunk
        res_text = f"Fix: {payload.confirmed_fix}\nRoot Cause: {payload.root_cause_summary}"
        if payload.affected_component:
            res_text += f"\nComponent: {payload.affected_component}"
            
        chunks.append(Chunk(
            bug_id=bug.id,
            source=source_name,
            chunk_type="resolution",
            text=res_text,
            chunk_index=0
        ))
        
        # 2. Create Description/Error Chunk
        desc_text = f"Title: {bug.title}\n"
        if bug.description:
            desc_text += f"Description: {bug.description}\n"
        if bug.stack_trace:
            desc_text += f"Stack Trace: {bug.stack_trace}\n"
        if bug.logs:
            desc_text += f"Logs: {bug.logs}\n"
            
        chunks.append(Chunk(
            bug_id=bug.id,
            source=source_name,
            chunk_type="description",
            text=desc_text[:3000], # Limit to avoid massive chunks
            chunk_index=1
        ))
        
        # Index
        added = vector_store.index_chunks(chunks)
        
        # Update db statuses
        bug.status = "resolved"
        
        # Update JSONB securely
        state_data = dict(diag.state) if diag.state else {}
        state_data["resolution"] = {
            "confirmed_fix": payload.confirmed_fix,
            "root_cause_summary": payload.root_cause_summary,
            "affected_component": payload.affected_component,
            "indexed_at": datetime.utcnow().isoformat()
        }
        diag.state = state_data
        
        session.commit()
        return {"status": "indexed", "chunks_added": added, "bug_id": bug.id}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/resolved")
def list_resolved_bugs():
    session = get_session()
    try:
        bugs = session.scalars(
            select(BugSubmission).where(BugSubmission.status == "resolved")
        ).all()
        return [
            {
                "id": b.id,
                "title": b.title,
                "created_at": b.created_at
            } for b in bugs
        ]
    finally:
        session.close()


@router.get("/status")
def knowledge_base_status():
    return {"indexed_chunk_count": vector_store.collection_count()}
