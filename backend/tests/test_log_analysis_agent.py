# backend/tests/test_log_analysis_agent.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.log_analysis_agent import analyze_log

JAVA_TRACE = """java.lang.NullPointerException: Cannot invoke method on null object
    at com.example.UserService.getEmail(UserService.java:42)
    at com.example.controller.UserController.handle(UserController.java:88)"""

PYTHON_TRACE = """Traceback (most recent call last):
  File "/app/main.py", line 10, in <module>
    process()
  File "/app/main.py", line 6, in process
    return 1 / 0
ZeroDivisionError: division by zero"""

JS_TRACE = """TypeError: Cannot read property 'email' of null
    at getUserEmail (/app/user.js:15:22)
    at Object.<anonymous> (/app/index.js:8:5)"""

GENERIC_LOG = "INFO starting up\nWARNING cache miss\nFATAL: disk quota exceeded, aborting write"


def test_java_stack_trace():
    r = analyze_log(stack_trace=JAVA_TRACE)
    assert r.format_detected == "java"
    assert r.exception_type == "java.lang.NullPointerException"
    assert r.failure_point["method"] == "getEmail"
    assert r.failure_point["line"] == 42
    assert len(r.code_path) == 2
    assert r.confidence_score > 0.9


def test_python_traceback_failure_point_is_innermost_frame():
    r = analyze_log(stack_trace=PYTHON_TRACE)
    assert r.format_detected == "python"
    assert r.exception_type == "ZeroDivisionError"
    # The actual failing frame is `process` at line 6, NOT `<module>` at line 10
    # (Python tracebacks list frames outermost-call-first).
    assert r.failure_point["method"] == "process"
    assert r.failure_point["line"] == 6


def test_javascript_stack_trace():
    r = analyze_log(stack_trace=JS_TRACE)
    assert r.format_detected == "javascript"
    assert r.exception_type == "TypeError"
    assert r.failure_point["method"] == "getUserEmail"
    assert r.failure_point["line"] == 15


def test_python_exception_not_ending_in_error_or_exception():
    """
    Real Python exceptions don't all end in Error/Exception/Warning
    (NoResultFound, StopIteration, etc.) — this must still be detected by
    the traceback's structure, not by keyword-matching the class name.
    Also covers: an unrelated log line appended after the traceback must
    not be mistaken for the exception header.
    """
    trace = (
        "Traceback (most recent call last):\n"
        '  File "app/routes/auth.py", line 48, in login\n'
        "    user = db.query(User).filter(User.email == payload.email).one()\n"
        '  File "sqlalchemy/orm/query.py", line 2808, in one\n'
        "    return self._iter().one()\n"
        "sqlalchemy.exc.NoResultFound: No row was found when one was required"
    )
    unrelated_trailing_log = "POST /api/auth/login 500 Internal Server Error"

    r = analyze_log(stack_trace=trace, error_log=unrelated_trailing_log)
    assert r.exception_type == "sqlalchemy.exc.NoResultFound"
    assert r.failure_point["method"] == "one"
    assert r.failure_point["line"] == 2808


def test_generic_log_without_stack_trace():
    r = analyze_log(stack_trace=GENERIC_LOG)
    assert r.format_detected == "generic"
    assert "disk quota exceeded" in r.error_message
    assert r.failure_point is None
    assert 0 < r.confidence_score < 0.5


def test_empty_input_does_not_crash():
    r = analyze_log(stack_trace="", error_log="")
    assert r.format_detected == "none"
    assert r.confidence_score == 0.0
    assert r.warnings


def test_unrecognized_gibberish_input():
    r = analyze_log(stack_trace="asdkjfh 12903 !!! not a stack trace at all")
    assert r.format_detected == "unrecognized"
    assert r.confidence_score < 0.2
