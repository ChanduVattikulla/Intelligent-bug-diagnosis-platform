# backend/app/agents/log_analysis_agent.py
"""
Log Analysis Agent .

Parses a stack trace / error log and extracts:
  - exception_type      e.g. "NullPointerException", "TypeError"
  - error_message        the text alongside the exception
  - failure_point         {file, class_or_module, method, line} of the top frame
  - code_path              ordered list of frames (file/method/line), most-recent-call first
  - confidence_score        how much structure was actually recoverable
  - format_detected        which parser matched ("python" | "java" | "javascript" | "generic")
  - warnings                 e.g. "no stack trace provided", "unrecognized format"

Design: regex-based rather than LLM-based on purpose — stack trace syntax is
regular and language-specific, so a parser is more reliable, faster, and
testable offline than an LLM call for this particular sub-problem. This
keeps the whole agent deterministic: same input always gives the same output,
which matters for M2.4's accuracy validation.
"""

import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class StackFrame:
    file: str
    method: str = ""
    class_name: str = ""
    line: Optional[int] = None


@dataclass
class LogAnalysisResult:
    exception_type: str = ""
    error_message: str = ""
    failure_point: Optional[dict] = None
    code_path: List[dict] = field(default_factory=list)
    format_detected: str = "none"
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Language-specific patterns
# ---------------------------------------------------------------------------

# Java: "at package.Class.method(File.java:123)"
_JAVA_FRAME_RE = re.compile(
    r"^\s*at\s+(?P<class>[\w.$]+)\.(?P<method><init>|<clinit>|\w+)\((?P<file>[\w.$]+\.java):(?P<line>\d+)\)"
)
# Java exception header: "java.lang.NullPointerException: message" or "Caused by: ..."
# Uses search (not full-line match) since people often paste exceptions inline,
# e.g. "Actual: java.lang.NullPointerException: foo" — the exception name isn't
# always the first thing on the line.
_JAVA_EXC_RE = re.compile(
    r"(?:Caused by:\s*)?(?P<exc>(?:[\w]+\.)*\w*(?:Exception|Error))\b\s*(?::\s*(?P<msg>[^\n]*))?"
)

# Python: 'File "path/to/file.py", line 42, in function_name'
_PYTHON_FRAME_RE = re.compile(
    r'^\s*File\s+"(?P<file>[^"]+)",\s*line\s+(?P<line>\d+),\s*in\s+(?P<method>.+?)\s*$'
)
# Note: there is no keyword-based Python exception regex — see _try_python,
# which identifies the exception header structurally (last non-indented line)
# instead, since not all exception names end in Error/Exception/Warning.

# JavaScript/Node: "at functionName (file.js:12:34)" or "at file.js:12:34" —
# column number is optional since not every trace/tool includes it.
_JS_FRAME_RE = re.compile(
    r"^\s*at\s+(?:(?P<method>[\w.$<>\[\] ]+?)\s*\()?(?P<file>[^\s()]+?):(?P<line>\d+)(?::(?P<col>\d+))?\)?\s*$"
)
# JS exception header: "TypeError: Cannot read property 'x' of undefined"
# Search-based for the same reason as the Java pattern above.
_JS_EXC_RE = re.compile(r"(?P<exc>\w*(?:Error|Exception))\b\s*(?::\s*(?P<msg>[^\n]*))?")

# Generic fallback: any line that looks like a log-level error message.
_GENERIC_ERROR_RE = re.compile(
    r"(?:^|\s)(?P<level>FATAL|ERROR|CRITICAL)\b[:\s-]*\s*(?P<msg>.+)$", re.IGNORECASE
)

MAX_CODE_PATH_FRAMES = 8


def _try_java(lines: List[str]) -> Optional[LogAnalysisResult]:
    frames = []
    exc_type, message = "", ""
    for line in lines:
        m = _JAVA_FRAME_RE.match(line)
        if m:
            frames.append(
                StackFrame(
                    file=m.group("file"),
                    class_name=m.group("class"),
                    method=m.group("method"),
                    line=int(m.group("line")),
                )
            )
            continue
        m = _JAVA_EXC_RE.search(line.strip())
        if m and not exc_type:  # take the first (outermost/original) exception found
            exc_type = m.group("exc")
            message = (m.group("msg") or "").strip()

    if not frames and not exc_type:
        return None

    return _build_result(exc_type, message, frames, "java")


def _try_python(lines: List[str]) -> Optional[LogAnalysisResult]:
    frame_matches = []  # (line_index, StackFrame)
    for i, line in enumerate(lines):
        m = _PYTHON_FRAME_RE.match(line)
        if m:
            frame_matches.append(
                (i, StackFrame(file=m.group("file"), method=m.group("method"), line=int(m.group("line"))))
            )

    # The exception header isn't identified by keyword (real exception names
    # don't all end in "Error"/"Exception"/"Warning" — e.g. NoResultFound,
    # StopIteration). Instead, use the actual structure of a Python
    # traceback: right after the LAST frame (skipping its one indented
    # source-context line, if present), the next non-indented line is the
    # exception header. Bounding the search to "right after the last frame"
    # (rather than "the last line of all provided text") matters when a
    # stack trace and an unrelated error log are concatenated together.
    exc_type, message = "", ""
    has_traceback_marker = any("traceback (most recent call last)" in l.lower() for l in lines)
    if frame_matches or has_traceback_marker:
        search_start = frame_matches[-1][0] + 1 if frame_matches else 0
        for line in lines[search_start:]:
            if not line.strip():
                continue
            if _PYTHON_FRAME_RE.match(line):
                break  # ran into another frame — no exception header found for this one
            if line.startswith((" ", "\t")):
                continue  # indented source-context line under the last frame — skip it
            # First non-indented, non-frame, non-blank line after the last frame.
            if ":" in line:
                exc_type, message = line.split(":", 1)
                exc_type, message = exc_type.strip(), message.strip()
            else:
                exc_type = line.strip()
            break

    frames = [f for _, f in frame_matches]
    if not frames and not exc_type:
        return None

    # Python lists frames outermost-call-first, so the actual failure site is
    # the LAST frame, not the first — reverse so downstream logic (and the
    # code_path docstring contract of "most-recent-call first") stays
    # consistent with how Java/JS stack traces are naturally ordered.
    frames.reverse()
    return _build_result(exc_type, message, frames, "python")


def _try_javascript(lines: List[str]) -> Optional[LogAnalysisResult]:
    frames = []
    exc_type, message = "", ""
    for line in lines:
        m = _JS_FRAME_RE.match(line)
        if m:
            frames.append(
                StackFrame(
                    file=m.group("file"),
                    method=(m.group("method") or "").strip(),
                    line=int(m.group("line")),
                )
            )
            continue
        m = _JS_EXC_RE.search(line.strip())
        if m and not exc_type:
            exc_type = m.group("exc")
            message = (m.group("msg") or "").strip()

    if not frames and not exc_type:
        return None

    return _build_result(exc_type, message, frames, "javascript")


def _try_generic(lines: List[str]) -> Optional[LogAnalysisResult]:
    for line in lines:
        m = _GENERIC_ERROR_RE.search(line)
        if m:
            return LogAnalysisResult(
                exception_type="",
                error_message=m.group("msg").strip(),
                failure_point=None,
                code_path=[],
                format_detected="generic",
                confidence_score=0.25,
                warnings=["No structured stack trace found; extracted a log line only."],
            )
    return None


def _build_result(exc_type: str, message: str, frames: List[StackFrame], fmt: str) -> LogAnalysisResult:
    top_frame = frames[0] if frames else None
    warnings = []

    # Confidence: start low, add credit for each piece of structure we recovered.
    score = 0.1
    if exc_type:
        score += 0.35
    else:
        warnings.append("Could not identify an exception/error type.")
    if message:
        score += 0.15
    if top_frame:
        score += 0.3
    else:
        warnings.append("Could not identify a failure point (file/method/line).")
    if len(frames) > 1:
        score += 0.1
    score = round(min(score, 0.97), 2)

    return LogAnalysisResult(
        exception_type=exc_type,
        error_message=message,
        failure_point=asdict(top_frame) if top_frame else None,
        code_path=[asdict(f) for f in frames[:MAX_CODE_PATH_FRAMES]],
        format_detected=fmt,
        confidence_score=score,
        warnings=warnings,
    )


def analyze_log(stack_trace: str = "", error_log: str = "") -> LogAnalysisResult:
    """
    Main entry point. Combines stack_trace + error_log (either may be empty)
    and tries each language parser, keeping whichever produces the most
    complete result. Never raises — worst case returns a low-confidence,
    mostly-empty result with a warning explaining why.
    """
    combined_text = "\n".join(t for t in [stack_trace or "", error_log or ""] if t.strip())

    if not combined_text.strip():
        return LogAnalysisResult(
            format_detected="none",
            confidence_score=0.0,
            warnings=["No stack trace or error log was provided."],
        )

    lines = combined_text.splitlines()

    candidates = []
    for parser in (_try_java, _try_python, _try_javascript):
        try:
            result = parser(lines)
        except Exception:
            # A parser bug should never take down the whole request — just skip it.
            result = None
        if result:
            candidates.append(result)

    if candidates:
        # Prefer whichever parser recovered the most structure.
        return max(candidates, key=lambda r: r.confidence_score)

    generic = _try_generic(lines)
    if generic:
        return generic

    return LogAnalysisResult(
        format_detected="unrecognized",
        confidence_score=0.05,
        warnings=["Text was provided but did not match any known log/stack-trace format."],
    )
