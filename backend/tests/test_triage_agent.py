# backend/tests/test_triage_agent.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.triage_agent import triage_bug, SEVERITY_LEVELS, PRIORITY_LEVELS


def test_critical_security_bug():
    r = triage_bug(
        title="Security vulnerability in login",
        description="Production database credentials exposed via security vulnerability, affecting all users, urgent fix needed",
    )
    assert r.severity == "Critical"
    assert r.component == "Security"
    assert r.priority == "P1"
    assert r.confidence_score > 0.5


def test_high_severity_backend_crash():
    r = triage_bug(
        title="API crash",
        description="API endpoint throws NullPointerException and crashes the server on every request",
    )
    assert r.severity == "High"
    assert r.component == "API/Backend"


def test_low_severity_cosmetic_issue():
    r = triage_bug(
        title="Typo",
        description="Typo in the settings page button label, minor visual issue",
    )
    assert r.severity == "Low"
    assert r.component == "Frontend/UI"


def test_authentication_component_detected():
    r = triage_bug(
        title="Login broken",
        description="Users cannot log in, password reset token API returns 500 error intermittently",
    )
    assert r.component == "Authentication"


def test_urgency_language_escalates_priority():
    baseline = triage_bug(title="x", description="The app fails and shows an exception")
    urgent = triage_bug(title="x", description="The app fails and shows an exception, this is urgent")
    assert PRIORITY_LEVELS.index(urgent.priority) <= PRIORITY_LEVELS.index(baseline.priority)


def test_empty_input_returns_safe_default_not_a_crash():
    r = triage_bug(title="", description="", stack_trace="", error_log="")
    assert r.severity in SEVERITY_LEVELS
    assert r.priority in PRIORITY_LEVELS
    assert r.confidence_score < 0.3


def test_reasoning_is_never_empty():
    r = triage_bug(title="Something broke", description="It just doesn't work anymore")
    assert isinstance(r.reasoning, str) and len(r.reasoning) > 0
