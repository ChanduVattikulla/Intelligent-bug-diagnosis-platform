# backend/app/orchestration/orchestrator.py
"""
Multi-Agent Orchestration (M2.3).

Runs the Triage Agent and Log Analysis Agent against a submitted bug and
combines their outputs into one structured "bug context" object. This
context is what gets stored alongside the bug report and is the shape that
Milestone 3's downstream agents (Duplicate Detection, Root Cause,
Remediation) will consume.

Error handling policy: a failure in one agent must never take down the
other, and must never take down the request. Each agent runs independently;
if one raises, its section of the context records the failure instead of
propagating the exception. This matters because in production, a malformed
or unusual bug report should degrade the analysis, not crash submission.
"""

from dataclasses import dataclass, asdict
from typing import Callable, Optional

from app.agents.triage_agent import triage_bug, TriageResult
from app.agents.log_analysis_agent import analyze_log, LogAnalysisResult
from app.agents.root_cause_agent import infer_root_cause
from app.agents.duplicate_detection_agent import detect_duplicates
from app.agents.remediation_agent import recommend_remediation
from app.services.llm_service import generate_findings, is_configured


@dataclass
class AgentOutcome:
    """Wraps one agent's result along with whether it actually ran successfully."""
    status: str  # "ok" | "skipped" | "error"
    result: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class BugContext:
    bug_id: str
    triage: AgentOutcome
    log_analysis: AgentOutcome
    root_cause: Optional[AgentOutcome] = None
    duplicate_detection: Optional[AgentOutcome] = None
    remediation: Optional[AgentOutcome] = None

    def to_dict(self) -> dict:
        return {
            "bug_id": self.bug_id,
            "triage": asdict(self.triage),
            "log_analysis": asdict(self.log_analysis),
            "root_cause": asdict(self.root_cause) if self.root_cause else None,
            "duplicate_detection": asdict(self.duplicate_detection) if self.duplicate_detection else None,
            "remediation": asdict(self.remediation) if self.remediation else None,
        }


def _run_triage(title: str, description: str, stack_trace: str, error_log: str, progress: Optional[Callable] = None) -> AgentOutcome:
    if progress:
        progress("Triage Agent", "working")
    try:
        result: TriageResult = triage_bug(
            title=title, description=description, stack_trace=stack_trace, error_log=error_log
        )
        outcome = AgentOutcome(status="ok", result=result.to_dict())
        if progress:
            progress("Triage Agent", "completed")
        return outcome
    except Exception as e:  # noqa: BLE001 - intentionally broad: agent failures must not propagate
        if progress:
            progress("Triage Agent", "error")
        return AgentOutcome(status="error", error=f"Triage Agent failed: {e}")


def _run_log_analysis(description: str, stack_trace: str, error_log: str, progress: Optional[Callable] = None) -> AgentOutcome:
    if progress:
        progress("Log Analysis Agent", "working")
    # Real users very often paste a stack trace as part of free-text
    # description rather than in a separate field (e.g. a single chat
    # message, a copy-pasted GitHub issue). Feed all three sources in —
    # the regex parsers only match actual stack-trace/exception syntax
    # wherever it appears, so this is safe even when description is just
    # plain prose with no trace in it at all.
    combined = "\n".join(t for t in [description, stack_trace, error_log] if (t or "").strip())

    if not combined.strip():
        # Not an error — plenty of legitimate bug reports have no logs at all.
        # Still return a valid empty result so downstream consumers have a
        # consistent shape to read regardless of whether logs were provided.
        empty = LogAnalysisResult(
            format_detected="none",
            confidence_score=0.0,
            warnings=["No stack trace or error log was provided."],
        )
        outcome = AgentOutcome(status="skipped", result=empty.to_dict())
        if progress:
            progress("Log Analysis Agent", "completed")
        return outcome

    try:
        result: LogAnalysisResult = analyze_log(stack_trace=combined)
        outcome = AgentOutcome(status="ok", result=result.to_dict())
        if progress:
            progress("Log Analysis Agent", "completed")
        return outcome
    except Exception as e:  # noqa: BLE001
        if progress:
            progress("Log Analysis Agent", "error")
        return AgentOutcome(status="error", error=f"Log Analysis Agent failed: {e}")


def run_orchestration(
    bug_id: str,
    title: str = "",
    description: str = "",
    stack_trace: str = "",
    error_log: str = "",
    progress: Optional[Callable] = None,
) -> BugContext:
    """
    Runs both agents and returns a combined BugContext. Invalid/missing
    input (empty strings) is handled gracefully by each agent individually —
    this function itself never raises.
    """
    triage_outcome = _run_triage(title, description, stack_trace, error_log, progress)
    log_outcome = _run_log_analysis(description, stack_trace, error_log, progress)

    return BugContext(bug_id=bug_id, triage=triage_outcome, log_analysis=log_outcome)


def run_milestone_three(context: BugContext, matches: list[dict], progress: Optional[Callable] = None) -> BugContext:
    """Run retrieval-backed M3 agents after the M2 context is available."""
    plain_context = context.to_dict()
    try:
        if progress:
            progress("Root Cause Agent", "working")
        root = infer_root_cause(plain_context, matches)
        root_outcome = AgentOutcome(status=root.status, result=root.to_dict())
        if progress:
            progress("Root Cause Agent", "completed")
    except Exception as exc:  # noqa: BLE001
        if progress:
            progress("Root Cause Agent", "error")
        root_outcome = AgentOutcome(status="error", error=f"Root Cause Agent failed: {exc}")
    try:
        if progress:
            progress("Duplicate Detection Agent", "working")
        duplicate = detect_duplicates(matches)
        duplicate_outcome = AgentOutcome(status="ok", result=duplicate.to_dict())
        if progress:
            progress("Duplicate Detection Agent", "completed")
    except Exception as exc:  # noqa: BLE001
        if progress:
            progress("Duplicate Detection Agent", "error")
        duplicate_outcome = AgentOutcome(status="error", error=f"Duplicate Detection Agent failed: {exc}")
    try:
        if progress:
            progress("Remediation Agent", "working")
        remediation = recommend_remediation(
            plain_context,
            root_outcome.result or {},
            duplicate_outcome.result or {},
            matches,
        )
        remediation_outcome = AgentOutcome(status=remediation.status, result=remediation.to_dict())
        if progress:
            progress("Remediation Agent", "completed")
    except Exception as exc:  # noqa: BLE001
        if progress:
            progress("Remediation Agent", "error")
        remediation_outcome = AgentOutcome(status="error", error=f"Remediation Agent failed: {exc}")
    context.root_cause = root_outcome
    context.duplicate_detection = duplicate_outcome
    context.remediation = remediation_outcome
    if is_configured():
        try:
            hosted = generate_findings(plain_context, matches)
            if isinstance(hosted.get("root_cause"), dict):
                context.root_cause = AgentOutcome(status=hosted["root_cause"].get("status", "supported"), result=hosted["root_cause"])
            if isinstance(hosted.get("remediation"), dict):
                context.remediation = AgentOutcome(status=hosted["remediation"].get("status", "supported"), result=hosted["remediation"])
        except Exception as exc:  # noqa: BLE001 - local fallback is intentional
            context.root_cause.error = f"Hosted reasoning unavailable; local evidence reasoning used: {exc}"
            context.remediation.error = f"Hosted reasoning unavailable; local evidence reasoning used: {exc}"
    return context
