#!/usr/bin/env python
"""
M2.4 — Accuracy Validation & Testing.

Two separate evaluations:

1. Triage Agent severity accuracy, against REAL ground-truth labels from the
   historical Eclipse/Mozilla/Apache datasets in data/raw/. Their bug
   trackers label "Priority" (Bugzilla P1-P5, or Apache
   Blocker/Critical/Major/Minor), not our exact Severity scale
   (Critical/High/Medium/Low) — PRIORITY_TO_SEVERITY below is an explicit,
   documented approximation for validation purposes, not a claim that the
   two scales are equivalent.

2. Log Analysis Agent accuracy, against a small hand-labeled test set built
   to specifically cover what M2.4 asks for: description-only bugs,
   description+stack-trace bugs, log-only bugs, and messy/unstructured logs,
   across Python/Java/JS formats.

Run from backend/: python scripts/validate_agents.py
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.config import RAW_DATA_DIR
from app.services.data_cleaning import standardize_dataframe
from app.agents.triage_agent import triage_bug
from app.agents.log_analysis_agent import analyze_log

# ---------------------------------------------------------------------------
# 1. Triage Agent vs. real historical labels
# ---------------------------------------------------------------------------

# Documented approximation — see module docstring.
PRIORITY_TO_SEVERITY = {
    "P1": "Critical", "P2": "High", "P3": "Medium", "P4": "Medium", "P5": "Low",
    "Blocker": "Critical", "Critical": "Critical", "Major": "High",
    "Minor": "Low", "Trivial": "Low",
}


def evaluate_triage_against_real_data():
    print("=" * 70)
    print("1. TRIAGE AGENT — severity accuracy vs. real historical Priority labels")
    print("=" * 70)

    all_rows = []
    for csv_path in sorted(RAW_DATA_DIR.glob("*.csv")):
        source = csv_path.stem.replace("_real", "")
        df = pd.read_csv(csv_path)
        cleaned = standardize_dataframe(df, source=source)
        all_rows.append(cleaned)
    data = pd.concat(all_rows, ignore_index=True)

    correct, total, confusion = 0, 0, Counter()
    misses = []

    for _, row in data.iterrows():
        expected = PRIORITY_TO_SEVERITY.get(row["priority"])
        if not expected:
            continue  # skip rows with an unmapped/missing priority label

        result = triage_bug(
            title=row["summary"], description=row["description"], stack_trace=row["stack_trace"]
        )
        total += 1
        confusion[(expected, result.severity)] += 1
        if result.severity == expected:
            correct += 1
        else:
            misses.append((row["bug_id"], expected, result.severity, row["summary"][:70]))

    accuracy = correct / total if total else 0.0
    print(f"Evaluated {total} real historical bugs with a mappable priority label.")
    print(f"Severity accuracy: {correct}/{total} = {accuracy:.1%}\n")

    print("Confusion (expected -> predicted): count")
    for (expected, predicted), count in sorted(confusion.items()):
        marker = "" if expected == predicted else "  <-- miss"
        print(f"  {expected:8s} -> {predicted:8s} : {count}{marker}")

    if misses:
        print(f"\nSample incorrect predictions ({min(5, len(misses))} of {len(misses)}):")
        for bug_id, expected, predicted, summary in misses[:5]:
            print(f"  [{bug_id}] expected={expected} got={predicted} — \"{summary}\"")

    print(
        "KNOWN LIMITATION: keyword substring matching means any variant of \"exception\"\n"
        "(e.g. \"NullPointerException\") always matches the generic \"exception\" keyword,\n"
        "so removing specific exception-name keywords doesn't change scoring — the word is\n"
        "still present as a substring. More importantly, many real bug titles are terse\n"
        "(\"NullPointerException in X\") with no explicit severity language at all; the real\n"
        "severity depends on deployment context (e.g. \"during test-suite shutdown\" vs.\n"
        "\"during user login\") that plain keyword matching cannot see. This is the expected\n"
        "ceiling for a rule-based agent — see the LLM swap-in note in triage_agent.py's\n"
        "docstring for the natural next step to push past it.\n"
    )
    return accuracy


# ---------------------------------------------------------------------------
# 2. Log Analysis Agent vs. a hand-labeled multi-format test set
# ---------------------------------------------------------------------------

LOG_ANALYSIS_TEST_CASES = [
    {
        "name": "Java NPE, description + stack trace",
        "stack_trace": (
            "java.lang.NullPointerException: session is null\n"
            "    at com.example.Auth.login(Auth.java:55)"
        ),
        "expected_exception_type": "java.lang.NullPointerException",
        "expected_failure_line": 55,
    },
    {
        "name": "Python ZeroDivisionError, stack-trace only",
        "stack_trace": (
            'Traceback (most recent call last):\n'
            '  File "/app/main.py", line 10, in <module>\n'
            "    process()\n"
            '  File "/app/main.py", line 6, in process\n'
            "    return 1 / 0\n"
            "ZeroDivisionError: division by zero"
        ),
        "expected_exception_type": "ZeroDivisionError",
        "expected_failure_line": 6,
    },
    {
        "name": "JS TypeError from a log file upload",
        "stack_trace": "",
        "error_log": (
            "TypeError: Cannot read property 'email' of null\n"
            "    at getUserEmail (/app/user.js:15:22)"
        ),
        "expected_exception_type": "TypeError",
        "expected_failure_line": 15,
    },
    {
        "name": "Description only, no logs at all",
        "stack_trace": "",
        "error_log": "",
        "expected_exception_type": "",
        "expected_failure_line": None,
    },
    {
        "name": "Messy/unstructured log, no real stack trace",
        "stack_trace": "",
        "error_log": "asdkjfh something broke idk 12903 !!!",
        "expected_exception_type": "",
        "expected_failure_line": None,
    },
    {
        "name": "Generic FATAL log line, no stack trace",
        "stack_trace": "",
        "error_log": "2024-01-01 INFO boot\n2024-01-01 FATAL: disk quota exceeded",
        "expected_exception_type": "",
        "expected_failure_line": None,
    },
]


def evaluate_log_analysis():
    print("=" * 70)
    print("2. LOG ANALYSIS AGENT — accuracy vs. hand-labeled multi-format test set")
    print("=" * 70)

    correct_exception_type = 0
    correct_failure_line = 0
    total = len(LOG_ANALYSIS_TEST_CASES)

    for case in LOG_ANALYSIS_TEST_CASES:
        result = analyze_log(
            stack_trace=case.get("stack_trace", ""), error_log=case.get("error_log", "")
        )

        exc_ok = result.exception_type == case["expected_exception_type"]
        line_ok = (result.failure_point or {}).get("line") == case["expected_failure_line"]

        correct_exception_type += exc_ok
        correct_failure_line += line_ok

        status = "OK" if (exc_ok and line_ok) else "MISS"
        print(
            f"[{status}] {case['name']:45s} "
            f"exc_type={'ok' if exc_ok else 'WRONG':5s} "
            f"failure_line={'ok' if line_ok else 'WRONG':5s} "
            f"(confidence={result.confidence_score})"
        )

    print(f"\nException-type accuracy: {correct_exception_type}/{total} = {correct_exception_type/total:.1%}")
    print(f"Failure-line accuracy:   {correct_failure_line}/{total} = {correct_failure_line/total:.1%}\n")


if __name__ == "__main__":
    evaluate_triage_against_real_data()
    evaluate_log_analysis()
