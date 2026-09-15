# backend/app/routers/bug_submission.py
"""
Bug Submission Module (M1.3): accepts a bug report either as pasted text
(title + description + stack trace + error log) or as an uploaded file
(.txt/.log/.json), validates it, and stores it in SQLite.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app import database
from app.schemas import BugSubmitRequest, BugReportResponse, BugListResponse
from app.services.file_parser import extract_text, validate_upload, UnsupportedFileError, FileTooLargeError
from app.orchestration.orchestrator import run_orchestration

router = APIRouter(prefix="/api/bugs", tags=["bug-submission"])


def _new_bug_id() -> str:
    return f"bug_{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _analyze_and_store(record: dict) -> dict:
    """
    Runs the Triage + Log Analysis agents (M2.3) on a bug record, attaches
    the result under metadata['bug_context'], and persists it. Centralized
    here so both the paste and upload endpoints trigger analysis identically.
    """
    context = run_orchestration(
        bug_id=record["id"],
        title=record["title"],
        description=record["description"],
        stack_trace=record["stack_trace"],
        error_log=record["error_log"],
    )
    record["metadata"] = {"bug_context": context.to_dict()}
    database.insert_bug_report(record)
    return record


@router.post("/submit", response_model=BugReportResponse)
def submit_bug_report(payload: BugSubmitRequest):
    """Direct-paste submission: title + optional description/stack trace/error log."""
    if not payload.has_content():
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: description, stack trace, or error log.",
        )

    record = {
        "id": _new_bug_id(),
        "title": payload.title.strip(),
        "description": (payload.description or "").strip(),
        "stack_trace": (payload.stack_trace or "").strip(),
        "error_log": (payload.error_log or "").strip(),
        "source_type": "paste",
        "original_filename": None,
        "status": "submitted",
        "created_at": _now_iso(),
        "metadata": {},
    }
    return _analyze_and_store(record)


@router.post("/upload", response_model=BugReportResponse)
async def upload_bug_report(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
):
    """File-upload submission: a .txt/.log/.json file becomes the error_log field."""
    raw_bytes = await file.read()

    try:
        validate_upload(file.filename, len(raw_bytes))
    except UnsupportedFileError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))

    text_content = extract_text(file.filename, raw_bytes)
    if not text_content.strip():
        raise HTTPException(status_code=422, detail="The uploaded file appears to be empty.")

    record = {
        "id": _new_bug_id(),
        "title": title.strip(),
        "description": description.strip(),
        "stack_trace": "",
        "error_log": text_content,
        "source_type": "upload",
        "original_filename": file.filename,
        "status": "submitted",
        "created_at": _now_iso(),
        "metadata": {},
    }
    return _analyze_and_store(record)


@router.get("/{bug_id}", response_model=BugReportResponse)
def get_bug_report(bug_id: str):
    report = database.get_bug_report(bug_id)
    if not report:
        raise HTTPException(status_code=404, detail="Bug report not found.")
    return report


@router.get("", response_model=BugListResponse)
def list_bug_reports(limit: int = 50, offset: int = 0):
    reports = database.list_bug_reports(limit=limit, offset=offset)
    return {"total_returned": len(reports), "reports": reports}
