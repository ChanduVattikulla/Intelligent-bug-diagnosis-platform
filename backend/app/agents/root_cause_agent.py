"""Root-cause reasoning over triage, log analysis, and retrieved defects."""

from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class RootCauseResult:
    status: str = "insufficient_evidence"
    hypothesis: str = ""
    confidence_score: float = 0.0
    reasoning: str = ""
    supporting_evidence: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def infer_root_cause(context: Dict, matches: List[dict]) -> RootCauseResult:
    """Build a conservative hypothesis from retrieved historical evidence.

    This is intentionally deterministic until a hosted LLM is configured. It
    keeps retrieved facts separate from the agent's conclusion and never calls
    a low-signal match a confirmed root cause.
    """
    triage = (context.get("triage") or {}).get("result") or {}
    log = (context.get("log_analysis") or {}).get("result") or {}
    usable = [m for m in matches if m.get("similarity_score", 0) >= 0.35]
    evidence = [
        {
            "bug_id": m.get("source_bug_id") or m.get("metadata", {}).get("bug_id", ""),
            "source": m.get("source") or m.get("metadata", {}).get("source", "unknown"),
            "chunk_type": m.get("chunk_type") or m.get("metadata", {}).get("chunk_type", ""),
            "text": m.get("text", ""),
            "similarity_score": m.get("similarity_score", 0),
        }
        for m in usable[:5]
    ]
    if not evidence:
        return RootCauseResult(
            reasoning="No historical defect reached the evidence threshold.",
        )

    failure = log.get("failure_point") or {}
    location = ":".join(str(value) for value in [failure.get("file"), failure.get("line")] if value)
    signals = [value for value in [log.get("exception_type"), log.get("error_message"), location, triage.get("component")] if value]
    top = evidence[0]
    hypothesis = f"A {triage.get('component', 'component')} defect related to {' / '.join(signals[:3]) or 'the reported failure'} is the most probable cause."
    if top.get("chunk_type") == "resolution":
        hypothesis += " The closest historical resolution points to a similar implementation failure."
    confidence = min(0.9, round(0.35 + top["similarity_score"] * 0.45 + (0.1 if log.get("exception_type") else 0), 2))
    return RootCauseResult(
        status="supported" if confidence >= 0.55 else "low_confidence",
        hypothesis=hypothesis,
        confidence_score=confidence,
        reasoning="The hypothesis combines deterministic triage/log signals with the highest-ranked retrieved defect; retrieved text is shown as evidence below.",
        supporting_evidence=evidence,
    )