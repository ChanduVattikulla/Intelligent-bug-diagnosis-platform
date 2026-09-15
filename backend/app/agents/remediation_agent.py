"""Actionable remediation suggestions grounded in historical resolutions."""

from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class RemediationResult:
    status: str = "insufficient_evidence"
    recommendations: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def recommend_remediation(context: Dict, root_cause: Dict, duplicates: Dict, matches: List[dict]) -> RemediationResult:
    evidence = [m for m in matches if m.get("chunk_type") == "resolution" and m.get("text")]
    if not evidence:
        evidence = [m for m in (duplicates.get("matches") or []) if m.get("text")]
    if not evidence:
        return RemediationResult()
    triage = (context.get("triage") or {}).get("result") or {}
    root = root_cause.get("hypothesis") or "the reported root cause"
    recommendations = []
    for item in evidence[:3]:
        recommendations.append({
            "recommendation": f"Investigate and patch the {triage.get('component', 'affected')} code path implicated by {root}. Validate the change against the reported failure and regression tests.",
            "basis": "historical_resolution" if item.get("chunk_type") == "resolution" else "related_historical_defect",
            "supporting_bug_id": item.get("source_bug_id") or item.get("bug_id") or (item.get("metadata") or {}).get("bug_id", ""),
            "supporting_evidence": item.get("text", ""),
            "confidence_score": round(min(0.9, float(item.get("similarity_score", 0)) + 0.15), 2),
        })
    return RemediationResult(status="supported", recommendations=recommendations)