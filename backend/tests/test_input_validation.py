import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.input_validation import validate_diagnosis_text


def test_rejects_placeholder_text():
    assert validate_diagnosis_text("asdf", "asdf")


def test_rejects_short_uninformative_text():
    assert validate_diagnosis_text("x", "x")


def test_accepts_real_bug_description():
    assert validate_diagnosis_text(
        "Login crashes",
        "The login API raises a TypeError when the password field is missing.",
    ) is None


def test_accepts_stack_trace_signal():
    assert validate_diagnosis_text("Crash", "NullPointerException in AuthService") is None


def test_accepts_long_bug_report_with_stack_trace():
    long_desc = "Application crashes with NullPointerException when processing payment in OrderService. " * 3
    long_trace = "java.lang.NullPointerException: Cannot invoke method on null object\n  at com.example.OrderService.processPayment(OrderService.java:42)"
    assert validate_diagnosis_text("NullPointerException in OrderService.java", long_desc, long_trace) is None