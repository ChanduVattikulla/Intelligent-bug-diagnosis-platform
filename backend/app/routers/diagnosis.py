"""Persistent diagnosis sessions and follow-up conversation endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from app.db_models import BugSubmission, ConversationMessage, DiagnosisSession
from app.db_session import get_session
from app.orchestration.orchestrator import run_milestone_three, run_orchestration
from app.schemas import (
    BugSubmitRequest,
    DiagnosisCreateResponse,
    DiagnosisMessageRequest,
    DiagnosisMessageResponse,
)
from app.services.vector_store import search_similar
from app.services.file_parser import extract_text, validate_upload, UnsupportedFileError, FileTooLargeError
from app.services.llm_service import generate_followup, is_configured
from app.services.input_validation import validate_diagnosis_text
from app.services.diagnosis_jobs import create_job, finish_job, get_job, update_job

router = APIRouter(prefix="/api/diagnoses", tags=["diagnosis"])


def _now():
    return datetime.now(timezone.utc)


def _build_report(bug, context, matches, progress=None):
    context = run_milestone_three(context, matches, progress=progress)
    serialized = context.to_dict()
    return {
        "type": "diagnosis",
        "bugId": bug.id,
        "triage": serialized.get("triage"),
        "logAnalysis": serialized.get("log_analysis"),
        "rootCause": serialized.get("root_cause"),
        "duplicateDetection": serialized.get("duplicate_detection"),
        "remediation": serialized.get("remediation"),
        "matches": matches,
        "reasoningMode": "hosted_model" if is_configured() else "local_evidence_fallback",
        "nextSteps": "Review the evidence-backed hypotheses and validate the recommended change with a regression test.",
    }


def _bug_dict(bug):
    return {
        "id": bug.id,
        "title": bug.title,
        "description": bug.description or "",
        "stack_trace": bug.stack_trace or "",
        "error_log": bug.logs or "",
        "source_type": "upload" if bug.uploaded_file_path else "paste",
        "original_filename": bug.uploaded_file_path,
        "status": bug.status,
        "created_at": bug.created_at.isoformat() if bug.created_at else "",
        "metadata": {},
    }


def _create_diagnosis(title: str, description: str, stack_trace: str, error_log: str, filename: str = "", progress=None):
    validation_error = validate_diagnosis_text(title, description, stack_trace, error_log)
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    session = get_session()
    try:
        bug = BugSubmission(
            id=f"bug_{uuid.uuid4().hex[:12]}",
            title=title.strip(),
            description=description.strip(),
            stack_trace=stack_trace.strip(),
            logs=error_log.strip(),
            uploaded_file_path=filename or None,
            status="submitted",
            created_at=_now(),
        )
        session.add(bug)
        session.flush()
        context = run_orchestration(
            bug_id=bug.id,
            title=bug.title,
            description=bug.description or "",
            stack_trace=bug.stack_trace or "",
            error_log=bug.logs or "",
            progress=progress,
        )
        if progress:
            progress("Historical Retrieval", "working")
        matches = search_similar("\n".join(filter(None, [bug.title, bug.description, bug.stack_trace, bug.logs])))
        if progress:
            progress("Historical Retrieval", "completed")
            progress("Report Generation", "working")
        report = _build_report(bug, context, matches, progress=progress)
        if progress:
            progress("Report Generation", "completed")
        diagnosis = DiagnosisSession(id=f"diag_{uuid.uuid4().hex[:12]}", bug_id=bug.id, state=report)
        session.add(diagnosis)
        session.flush()
        session.add(ConversationMessage(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            diagnosis_id=diagnosis.id,
            role="assistant",
            content="Initial diagnosis generated.",
        ))
        session.commit()
        return {"session_id": diagnosis.id, "bug": _bug_dict(bug), "report": report}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("", response_model=DiagnosisCreateResponse)
def create_diagnosis(payload: BugSubmitRequest):
    return _create_diagnosis(
        payload.title,
        payload.description or "",
        payload.stack_trace or "",
        payload.error_log or "",
    )


def _run_diagnosis_job(job_id, title, description, stack_trace, error_log):
    try:
        result = _create_diagnosis(
            title,
            description,
            stack_trace,
            error_log,
            progress=lambda agent, status: update_job(job_id, agent, status),
        )
        finish_job(job_id, result=result)
    except Exception as exc:  # noqa: BLE001 - surfaced through the job status endpoint
        finish_job(job_id, error=str(exc))


@router.post("/start")
def start_diagnosis(payload: BugSubmitRequest):
    validation_error = validate_diagnosis_text(
        payload.title,
        payload.description or "",
        payload.stack_trace or "",
        payload.error_log or "",
    )
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)
    job_id = create_job(
        _run_diagnosis_job,
        payload.title,
        payload.description or "",
        payload.stack_trace or "",
        payload.error_log or "",
    )
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def diagnosis_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Diagnosis job not found.")
    return job


@router.post("/upload", response_model=DiagnosisCreateResponse)
async def create_uploaded_diagnosis(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
):
    raw_bytes = await file.read()
    try:
        validate_upload(file.filename, len(raw_bytes))
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    text_content = extract_text(file.filename, raw_bytes)
    if not text_content.strip():
        raise HTTPException(status_code=422, detail="The uploaded file appears to be empty.")
    return _create_diagnosis(title, description, "", text_content, file.filename or "")


@router.post("/{session_id}/messages", response_model=DiagnosisMessageResponse)
def add_message(session_id: str, payload: DiagnosisMessageRequest):
    session = get_session()
    try:
        diagnosis = session.get(DiagnosisSession, session_id)
        if diagnosis is None:
            raise HTTPException(status_code=404, detail="Diagnosis session not found.")

        history = [
            {"role": item.role, "content": item.content}
            for item in session.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.diagnosis_id == session_id)
                .order_by(ConversationMessage.created_at)
            ).all()
        ]
        session.add(ConversationMessage(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            diagnosis_id=session_id,
            role="user",
            content=payload.content.strip(),
        ))
        if is_configured():
            try:
                reply = generate_followup(diagnosis.state, history, payload.content.strip())
            except Exception as exc:  # noqa: BLE001 - preserve the saved conversation on provider failure
                err_str = str(exc).lower()
                if "402" in err_str or "credit" in err_str or "payment" in err_str:
                    reply = (
                        "I saved your question, but the AI provider could not answer because the account "
                        "has no available credit. Add credit to OpenRouter or switch to another model, then "
                        "try again."
                    )
                elif "404" in err_str or "not found" in err_str or "no such model" in err_str:
                    reply = (
                        "I saved your question, but the selected AI model is not available. "
                        "Check LLM_MODEL in backend/.env and restart the backend."
                    )
                elif "401" in err_str or "unauthorized" in err_str or "invalid api" in err_str:
                    reply = (
                        "I saved your question, but the AI provider rejected the API key. "
                        "Check LLM_API_KEY in backend/.env."
                    )
                else:
                    reply = (
                        "I saved your question, but the AI provider is temporarily unavailable. "
                        f"Error: {str(exc)[:200]}. Please try again in a moment."
                    )
        else:
            reply = "Follow-up saved. Configure LLM_API_KEY in backend/.env to enable AI-powered answers."
        message = {"id": f"msg_{uuid.uuid4().hex[:12]}", "role": "assistant", "content": reply}
        session.add(ConversationMessage(diagnosis_id=session_id, id=message["id"], role=message["role"], content=message["content"]))
        session.commit()
        return {"session_id": session_id, "message": message}
    finally:
        session.close()