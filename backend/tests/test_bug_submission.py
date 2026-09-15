# backend/tests/test_bug_submission.py
"""
Run with: pytest tests/ -v
(from inside backend/, with the venv activated)
"""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.db_models import BugSubmission, ConversationMessage, DiagnosisSession
from app.db_session import get_session


@pytest.fixture()
def client():
    with TestClient(app) as c:
        session = get_session()
        try:
            session.execute(delete(ConversationMessage))
            session.execute(delete(DiagnosisSession))
            session.execute(delete(BugSubmission))
            session.commit()
        finally:
            session.close()
        yield c


def test_health_check(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_submit_and_fetch_bug_report(client):
    r = client.post(
        "/api/bugs/submit",
        json={
            "title": "App crashes on null user object",
            "description": "Crashes when user.email is accessed on a null user.",
            "stack_trace": "TypeError: Cannot read property email of null",
        },
    )
    assert r.status_code == 200
    bug = r.json()
    assert bug["title"] == "App crashes on null user object"
    assert bug["source_type"] == "paste"

    r = client.get(f"/api/bugs/{bug['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == bug["id"]


def test_submit_rejects_empty_content(client):
    r = client.post("/api/bugs/submit", json={"title": "Nothing here"})
    assert r.status_code == 422


def test_list_bug_reports(client):
    client.post("/api/bugs/submit", json={"title": "Bug A", "description": "x"})
    client.post("/api/bugs/submit", json={"title": "Bug B", "description": "y"})
    r = client.get("/api/bugs")
    assert r.status_code == 200
    assert r.json()["total_returned"] == 2


def test_upload_accepts_supported_file_type(client):
    r = client.post(
        "/api/bugs/upload",
        files={"file": ("crash.log", io.BytesIO(b"Fatal error at line 42"), "text/plain")},
        data={"title": "Uploaded crash log"},
    )
    assert r.status_code == 200
    assert r.json()["original_filename"] == "crash.log"
    assert "Fatal error" in r.json()["error_log"]


def test_upload_rejects_unsupported_file_type(client):
    r = client.post(
        "/api/bugs/upload",
        files={"file": ("crash.exe", io.BytesIO(b"binary"), "application/octet-stream")},
        data={"title": "Bad file"},
    )
    assert r.status_code == 415


def test_upload_rejects_empty_file(client):
    r = client.post(
        "/api/bugs/upload",
        files={"file": ("empty.txt", io.BytesIO(b"   "), "text/plain")},
        data={"title": "Empty file"},
    )
    assert r.status_code == 422
