"""Semantic duplicate classification over historical defect matches."""

from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class DuplicateResult:
    status: str = "new_or_unmatched"
    threshold: float = 0.72
    matches: List[dict] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def detect_duplicates(matches: List[dict], top_k: int = 5) -> DuplicateResult:
    """Collapse chunk-level retrieval into ranked defect-level matches."""
    grouped = {}
    for match in matches:
        metadata = match.get("metadata") or {}
        bug_id = match.get("source_bug_id") or metadata.get("bug_id")
        if not bug_id:
            continue
        score = float(match.get("similarity_score", 0))
        current = grouped.get(bug_id)
        if current is None or score > current["similarity_score"]:
            grouped[bug_id] = {
                "bug_id": bug_id,
                "source": match.get("source") or metadata.get("source", "unknown"),
                "chunk_type": match.get("chunk_type") or metadata.get("chunk_type", ""),
                "text": match.get("text", ""),
                "similarity_score": round(score, 4),
                "resolution_summary": match.get("resolution_summary", ""),
            }
    ranked = sorted(grouped.values(), key=lambda item: item["similarity_score"], reverse=True)[:top_k]
    best = ranked[0]["similarity_score"] if ranked else 0
    status = "duplicate" if best >= 0.82 else "related" if best >= 0.62 else "new_or_unmatched"
    return DuplicateResult(
        status=status,
        matches=ranked,
        reasoning=(f"Top semantic match scored {best:.0%}; threshold-based classification is {status}." if ranked else "No semantic matches were retrieved."),
    )