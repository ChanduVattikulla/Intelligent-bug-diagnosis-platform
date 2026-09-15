"""SQLAlchemy storage for submitted bug reports."""

from datetime import datetime

from sqlalchemy import select

from app.db_models import BugSubmission
from app.db_session import create_all_tables, get_session


import sys

def init_db():
    """Create the PostgreSQL schema used by the application."""
    if not create_all_tables():
        print("Warning: Database initialization failed. Check DATABASE_URL in backend/.env.", file=sys.stderr)


def insert_bug_report(report: dict):
    session = get_session()
    try:
        created_at = report.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        record = BugSubmission(
            id=report["id"],
            title=report["title"],
            description=report.get("description") or "",
            stack_trace=report.get("stack_trace") or "",
            logs=report.get("error_log") or "",
            uploaded_file_path=report.get("original_filename"),
            status=report.get("status") or "submitted",
            created_at=created_at,
        )
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_bug_report(bug_id: str):
    session = get_session()
    try:
        record = session.get(BugSubmission, bug_id)
        return _record_to_dict(record) if record else None
    finally:
        session.close()

def list_bug_reports(limit: int = 50, offset: int = 0):
    session = get_session()
    try:
        statement = (
            select(BugSubmission)
            .order_by(BugSubmission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        records = session.scalars(statement).all()
        return [_record_to_dict(record) for record in records]
    finally:
        session.close()

def _record_to_dict(record: BugSubmission) -> dict:
    uploaded_file_path = record.uploaded_file_path
    return {
        "id": record.id,
        "title": record.title,
        "description": record.description or "",
        "stack_trace": record.stack_trace or "",
        "error_log": record.logs or "",
        "source_type": "upload" if uploaded_file_path else "paste",
        "original_filename": uploaded_file_path,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else "",
        "metadata": {},
    }
