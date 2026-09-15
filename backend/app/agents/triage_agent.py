# backend/app/agents/triage_agent.py
"""
Triage Agent .

Classifies a submitted bug by severity, priority, and affected component,
with a confidence score and a short human-readable reasoning string.

Design: keyword/rule-based rather than LLM-based, same rationale as the Log
Analysis Agent — deterministic, offline-testable, and gradeable against a
fixed test set without needing an API key. Each keyword match is recorded,
so "reasoning" is generated directly from what actually matched rather than
being a separate free-text explanation that could drift from the real logic.

Swapping in an LLM later: this module exposes a single function,
`triage_bug(title, description, stack_trace, error_log)`, returning a
TriageResult. An LLM-backed implementation could replace the body of that
function without changing any caller (see app/orchestration/orchestrator.py).
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]
PRIORITY_LEVELS = ["P1", "P2", "P3", "P4"]

# Each phrase is checked as a case-insensitive substring match against the
# combined bug text (title + description + stack trace + error log).
SEVERITY_KEYWORDS: Dict[str, List[str]] = {
    "Critical": [
        "data loss", "data corruption", "security vulnerability", "security breach",
        "cannot start", "won't start", "system down", "outage", "crash on startup",
        "unrecoverable", "exploit", "remote code execution",
        "all users affected", "production down",
    ],
    "High": [
        "crash", "crashes", "exception", "fails", "failure", "broken", "not working",
        "regression", "incorrect result", "blocks", "blocking", "500 error",
        "out of memory", "deadlock", "memory leak",
    ],
    "Medium": [
        "intermittent", "occasionally", "sometimes", "workaround available",
        "degraded", "slow", "performance issue", "minor data issue", "edge case",
    ],
    "Low": [
        "typo", "cosmetic", "visual glitch", "spelling", "minor ui issue",
        "suggestion", "enhancement", "nice to have", "documentation",
    ],
}

URGENCY_ESCALATION_KEYWORDS = [
    "urgent", "asap", "blocking release", "production", "customer-facing",
    "affects all users", "no workaround",
]

COMPONENT_KEYWORDS: Dict[str, List[str]] = {
    "Authentication": ["login", "log in", "logout", "auth", "password", "oauth", "session", "token", "sign in", "sign-in", "signin"],
    "Database": ["database", " sql ", "query", "db ", "record", "table", "migration", "deadlock", "transaction"],
    "API/Backend": ["api", "endpoint", "backend", "server error", "500 error", "request timeout", "rest api", "webhook"],
    "Frontend/UI": ["ui", "button", "page", "layout", "css", "render", "display", "screen", "frontend", "dropdown", "modal"],
    "Networking": ["network", "connection", "socket", "dns", " tcp ", "http error", "timeout", "unreachable"],
    "Performance": ["slow", "performance", "latency", "memory leak", "high cpu", "lag", "out of memory"],
    "Security": ["security", "vulnerability", "exploit", "injection", "xss", "csrf", "unauthorized access"],
    "Build/Deployment": ["build failed", "deploy", "deployment", "ci pipeline", "compile error", "docker", "pipeline failed"],
}

DEFAULT_COMPONENT = "Unspecified"


@dataclass
class TriageResult:
    severity: str = "Medium"
    priority: str = "P3"
    component: str = DEFAULT_COMPONENT
    confidence_score: float = 0.3
    reasoning: str = ""
    matched_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _score_categories(text: str, keyword_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Returns {category: [matched keywords]} for every category with >=1 match."""
    lowered = f" {text.lower()} "
    matches: Dict[str, List[str]] = {}
    for category, keywords in keyword_map.items():
        found = [kw for kw in keywords if kw.lower() in lowered]
        if found:
            matches[category] = found
    return matches


def _pick_best(matches: Dict[str, List[str]], ordered_priority: List[str]) -> str:
    """Among matched categories, prefer the most severe/first-listed one with the most hits."""
    if not matches:
        return ordered_priority[len(ordered_priority) // 2]  # a middle-of-the-road default
    # Sort by (severity rank in ordered_priority, number of matched keywords) descending.
    def sort_key(category):
        rank = ordered_priority.index(category) if category in ordered_priority else len(ordered_priority)
        return (-len(matches[category]), rank)

    return sorted(matches.keys(), key=sort_key)[0]


def triage_bug(title: str = "", description: str = "", stack_trace: str = "", error_log: str = "") -> TriageResult:
    """
    Main entry point. Never raises — a bug with no usable text at all still
    gets a valid (low-confidence, default) TriageResult rather than an error.
    """
    combined_text = " ".join(t for t in [title, description, stack_trace, error_log] if t)

    if not combined_text.strip():
        return TriageResult(
            severity="Medium",
            priority="P3",
            component=DEFAULT_COMPONENT,
            confidence_score=0.1,
            reasoning="No title, description, stack trace, or error log was provided — defaulted to Medium/P3/Unspecified.",
            matched_signals=[],
        )

    severity_matches = _score_categories(combined_text, SEVERITY_KEYWORDS)
    severity = _pick_best(severity_matches, SEVERITY_LEVELS)

    component_matches = _score_categories(combined_text, COMPONENT_KEYWORDS)
    component = _pick_best(component_matches, list(COMPONENT_KEYWORDS.keys())) if component_matches else DEFAULT_COMPONENT

    # Priority starts aligned with severity, then can escalate by one level
    # if urgency language is present (impact + urgency, per the milestone spec).
    base_priority_index = SEVERITY_LEVELS.index(severity)
    urgency_hits = [kw for kw in URGENCY_ESCALATION_KEYWORDS if kw in combined_text.lower()]
    priority_index = max(0, base_priority_index - (1 if urgency_hits else 0))
    priority = PRIORITY_LEVELS[priority_index]

    # Confidence: more matched keywords and a clearly-identified component both raise it.
    total_severity_hits = len(severity_matches.get(severity, []))
    confidence = 0.35 + min(0.35, 0.08 * total_severity_hits)
    if component != DEFAULT_COMPONENT:
        confidence += 0.15
    if urgency_hits:
        confidence += 0.05
    confidence = round(min(confidence, 0.95), 2)

    matched_signals = [f"severity:{kw}" for kw in severity_matches.get(severity, [])]
    matched_signals += [f"component:{kw}" for kw in component_matches.get(component, [])] if component_matches else []
    matched_signals += [f"urgency:{kw}" for kw in urgency_hits]

    reasoning_parts = []
    if severity_matches.get(severity):
        reasoning_parts.append(
            f"Classified as {severity} severity based on: {', '.join(severity_matches[severity])}."
        )
    else:
        reasoning_parts.append(f"No strong severity keywords matched; defaulted to {severity}.")

    if component != DEFAULT_COMPONENT:
        reasoning_parts.append(
            f"Matched {component} component based on: {', '.join(component_matches[component])}."
        )
    else:
        reasoning_parts.append("No component keywords matched; component left Unspecified.")

    if urgency_hits:
        reasoning_parts.append(
            f"Priority escalated to {priority} due to urgency language: {', '.join(urgency_hits)}."
        )
    else:
        reasoning_parts.append(f"Priority set to {priority}, aligned with severity.")

    return TriageResult(
        severity=severity,
        priority=priority,
        component=component,
        confidence_score=confidence,
        reasoning=" ".join(reasoning_parts),
        matched_signals=matched_signals,
    )
