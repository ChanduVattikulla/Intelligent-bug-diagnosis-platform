# backend/tests/test_orchestration.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.orchestration.orchestrator import run_orchestration


def test_full_bug_report_runs_both_agents_successfully():
    ctx = run_orchestration(
        bug_id="bug_1",
        title="Login crashes",
        description="Login page crashes with a null pointer exception, urgent",
        stack_trace="java.lang.NullPointerException\n    at com.example.Auth.login(Auth.java:10)",
    )
    assert ctx.triage.status == "ok"
    assert ctx.log_analysis.status == "ok"
    assert ctx.triage.result["severity"] in {"Critical", "High", "Medium", "Low"}
    assert ctx.log_analysis.result["exception_type"] == "java.lang.NullPointerException"


def test_description_only_bug_still_attempts_log_analysis():
    """
    Real users often paste a stack trace as part of free-text description
    rather than in a separate field — so a description-only submission should
    still be analyzed, just likely with low confidence if no trace is present.
    """
    ctx = run_orchestration(bug_id="bug_2", title="Slow page", description="The dashboard loads slowly")
    assert ctx.triage.status == "ok"
    assert ctx.log_analysis.status == "ok"
    assert ctx.log_analysis.result["confidence_score"] < 0.3  # no real trace in this text


def test_stack_trace_embedded_in_description_is_still_found():
    """The actual bug this fixes: a stack trace pasted inline as part of prose, not a separate field."""
    ctx = run_orchestration(
        bug_id="bug_2b",
        title="Login crashes",
        description=(
            "Steps: click submit with blank password.\n"
            "Actual: TypeError: Cannot read property 'trim' of undefined\n"
            "    at validateAuth (auth.js:42)"
        ),
    )
    assert ctx.log_analysis.status == "ok"
    assert ctx.log_analysis.result["exception_type"] == "TypeError"
    assert ctx.log_analysis.result["failure_point"]["line"] == 42


def test_completely_empty_submission_does_not_crash():
    """M2.3: 'error handling for ... invalid input'."""
    ctx = run_orchestration(bug_id="bug_3")
    assert ctx.triage.status == "ok"  # triage still returns a safe default
    assert ctx.log_analysis.status == "skipped"


def test_messy_unstructured_log_still_produces_a_result():
    ctx = run_orchestration(
        bug_id="bug_4",
        title="Something broke",
        error_log="asdkjfh random garbage !!! 12903",
    )
    assert ctx.log_analysis.status == "ok"
    assert ctx.log_analysis.result["confidence_score"] < 0.3  # low confidence, but no crash


def test_context_serializes_to_plain_dict():
    ctx = run_orchestration(bug_id="bug_5", title="x", description="crash")
    d = ctx.to_dict()
    assert d["bug_id"] == "bug_5"
    assert "triage" in d and "log_analysis" in d
