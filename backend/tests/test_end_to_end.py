import time
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def warmup_embedding_model():
    """Pre-load the sentence-transformers model before any test runs.
    Without this, the first job takes 70-80 s loading HuggingFace weights,
    causing any test with a 60-120 s timeout to fail on a cold process."""
    from app.services.embeddings import embed_text
    embed_text("warmup")  # forces model load once for the whole session


def wait_for_job(job_id: str, timeout: int = 120):
    start = time.time()
    while time.time() - start < timeout:
        res = client.get(f"/api/diagnoses/jobs/{job_id}")
        assert res.status_code == 200
        data = res.json()
        if data["status"] == "completed":
            return data["result"]
        if data["status"] == "failed":
            pytest.fail(f"Job failed: {data.get('error')}")
        time.sleep(2)
    pytest.fail(f"Job timed out after {timeout} seconds")


def submit_bug_and_wait(payload):
    res = client.post("/api/diagnoses/start", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    job_id = res.json()["job_id"]
    result = wait_for_job(job_id)
    return result


# ── Shared session fixture ────────────────────────────────────────────────────
# autouse=True so this runs BEFORE any individual test, warming up the full
# pipeline (DB connection pool, vector search, all agent code paths).
# This prevents test_text_submission_java_npe from hitting a cold-start timeout
# on the first real job submission. test_knowledge_base_resolve also uses this
# fixture directly to avoid submitting an extra redundant job.

@pytest.fixture(scope="session", autouse=True)
def shared_diagnosis():
    payload = {
        "title": "Shared: DB Connection Refused on startup",
        "description": "The application cannot connect to the database on startup",
        "stack_trace": "ConnectionRefusedError: [Errno 111] Connection refused\n  File 'db.py', line 44, in connect",
        "error_log": ""
    }
    return submit_bug_and_wait(payload)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_text_submission_java_npe():
    payload = {
        "title": "Java NullPointerException in UserService",
        "description": "App crashes when logging in",
        "stack_trace": "java.lang.NullPointerException\n\tat com.example.UserService.login(UserService.java:42)\n\tat com.example.AuthController.handleLogin(AuthController.java:18)",
        "error_log": ""
    }
    result = submit_bug_and_wait(payload)
    assert "session_id" in result
    report = result["report"]
    # Report structure: each section is an AgentOutcome {status, result, error}
    assert "triage" in report
    assert "logAnalysis" in report
    assert "rootCause" in report
    assert "duplicateDetection" in report
    assert "remediation" in report
    assert report["triage"]["status"] in ["ok", "error"]


def test_text_submission_python_keyerror():
    payload = {
        "title": "Python KeyError on user data",
        "description": "Getting KeyError when accessing user['email']",
        "stack_trace": "Traceback (most recent call last):\n  File 'main.py', line 10, in <module>\n    print(user['email'])\nKeyError: 'email'",
        "error_log": ""
    }
    result = submit_bug_and_wait(payload)
    report = result["report"]
    # logAnalysis is an AgentOutcome: {"status": "ok", "result": {...}, "error": null}
    log_result = report["logAnalysis"].get("result") or {}
    assert log_result.get("exception_type") == "KeyError"
    assert report["triage"]["result"]["severity"] in ["High", "Medium", "Critical", "Low"]


def test_insufficient_evidence_fallback():
    payload = {
        "title": "It is broken",
        "description": "I clicked the button and nothing happened.",
        "stack_trace": "",
        "error_log": ""
    }
    result = submit_bug_and_wait(payload)
    report = result["report"]
    # Should always produce a report even for vague bugs
    assert "triage" in report


def test_analytics_endpoint():
    res = client.get("/api/analytics/defects")
    assert res.status_code == 200
    data = res.json()
    required_keys = [
        "total_bugs", "severity_distribution", "component_distribution",
        "exception_type_distribution", "root_cause_distribution", "duplicate_rate",
        "bug_frequency_over_time", "top_recurring_components",
        "common_error_patterns", "knowledge_base_size", "remediation_supported_rate"
    ]
    for key in required_keys:
        assert key in data, f"Missing analytics key: {key}"


def test_knowledge_base_resolve(shared_diagnosis):
    """Uses a pre-submitted session so no additional job submission is needed."""
    session_id = shared_diagnosis["session_id"]

    resolve_payload = {
        "session_id": session_id,
        "confirmed_fix": "Added retry logic with exponential backoff and verified DB container health before connection.",
        "root_cause_summary": "Database container was not ready when the application attempted to connect at startup.",
        "affected_component": "Database"
    }

    res = client.post("/api/knowledge-base/resolve", json=resolve_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["indexed", "already_indexed"]

    if data["status"] == "indexed":
        assert data["chunks_added"] > 0
        assert "bug_id" in data
