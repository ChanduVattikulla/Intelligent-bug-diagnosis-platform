# backend/app/schemas.py
"""Request/response shapes for the API, validated automatically by FastAPI."""

from typing import Optional, List
from pydantic import BaseModel, Field


class BugSubmitRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=20000)
    stack_trace: Optional[str] = Field(default="", max_length=20000)
    error_log: Optional[str] = Field(default="", max_length=20000)

    def has_content(self) -> bool:
        return bool((self.description or self.stack_trace or self.error_log or "").strip())


class BugReportResponse(BaseModel):
    id: str
    title: str
    description: str
    stack_trace: str
    error_log: str
    source_type: str
    original_filename: Optional[str] = None
    status: str
    created_at: str
    metadata: dict = Field(default_factory=dict)


class BugListResponse(BaseModel):
    total_returned: int
    reports: List[BugReportResponse]


class DiagnosisCreateResponse(BaseModel):
    session_id: str
    bug: BugReportResponse
    report: dict


class DiagnosisMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)


class DiagnosisMessageResponse(BaseModel):
    session_id: str
    message: dict


class SimilarBugMatch(BaseModel):
    source_bug_id: str
    source: str            # e.g. "mozilla", "apache", "eclipse"
    chunk_type: str        # e.g. "description", "stack_trace", "resolution"
    text: str
    similarity_score: float
    metadata: dict


class KnowledgeBaseSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeBaseSearchResponse(BaseModel):
    query: str
    matches: List[SimilarBugMatch]
