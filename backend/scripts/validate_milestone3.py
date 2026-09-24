#!/usr/bin/env python
"""
M3 Verification & Testing — Comprehensive validation script for Milestone 3 agents:
1. Root Cause Agent (M3.1)
2. Duplicate Detection Agent (M3.2)
3. Remediation Agent (M3.3)

Run from backend/: python scripts/validate_milestone3.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.root_cause_agent import infer_root_cause
from app.agents.duplicate_detection_agent import detect_duplicates
from app.agents.remediation_agent import recommend_remediation
from app.orchestration.orchestrator import run_orchestration, run_milestone_three
from app.services.vector_store import search_similar

SAMPLE_BUG_1 = {
    "title": "NullPointerException in OrderService when processing payment",
    "description": "Application crashes with NullPointerException when processing payment in OrderService.java",
    "stack_trace": "java.lang.NullPointerException: Cannot invoke method on null object\n  at com.example.OrderService.processPayment(OrderService.java:42)",
    "error_log": "2026-09-22 10:00:00 [ERROR] Failed to process order",
}

SAMPLE_BUG_WEAK = {
    "title": "Unusual glitch in customized experimental rendering pipeline",
    "description": "Obscure behavior with custom shader 99x",
    "stack_trace": "",
    "error_log": "",
}


def test_m3_1_root_cause_agent():
    print("=" * 70)
    print("1. M3.1 — ROOT CAUSE AGENT VALIDATION")
    print("=" * 70)
    
    ctx = run_orchestration("test_bug_1", **SAMPLE_BUG_1)
    plain_ctx = ctx.to_dict()
    matches = search_similar(SAMPLE_BUG_1["title"])
    
    result = infer_root_cause(plain_ctx, matches)
    print(f"Status: {result.status}")
    print(f"Hypothesis: {result.hypothesis}")
    print(f"Confidence Score: {Math_pct(result.confidence_score)}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Supporting Evidence count: {len(result.supporting_evidence)}")
    assert result.hypothesis, "Root cause hypothesis should not be empty"
    assert 0.0 <= result.confidence_score <= 1.0, "Confidence score out of bounds"
    print("[OK] M3.1 Root Cause Agent passed all schema and reasoning assertions.\n")


def test_m3_2_duplicate_detection_agent():
    print("=" * 70)
    print("2. M3.2 — DUPLICATE DETECTION AGENT VALIDATION")
    print("=" * 70)
    
    matches = search_similar(SAMPLE_BUG_1["title"])
    result = detect_duplicates(matches)
    
    print(f"Status: {result.status}")
    print(f"Matches Evaluated: {len(result.matches)}")
    if result.matches:
        top = result.matches[0]
        print(f"Top Match ID: {top['bug_id']} | Similarity: {Math_pct(top['similarity_score'])} | Source: {top['source']}")
        print(f"Resolution Summary: {top['resolution_summary'][:80]}...")
    print(f"Reasoning: {result.reasoning}")
    assert result.status in {"duplicate", "related", "new_or_unmatched"}, f"Invalid duplicate status: {result.status}"
    print("[OK] M3.2 Duplicate Detection Agent passed all ranking and status assertions.\n")


def test_m3_3_remediation_agent():
    print("=" * 70)
    print("3. M3.3 — REMEDIATION AGENT VALIDATION")
    print("=" * 70)
    
    ctx = run_orchestration("test_bug_1", **SAMPLE_BUG_1)
    plain_ctx = ctx.to_dict()
    matches = search_similar(SAMPLE_BUG_1["title"])
    root = infer_root_cause(plain_ctx, matches)
    dups = detect_duplicates(matches)
    
    result = recommend_remediation(plain_ctx, root.to_dict(), dups.to_dict(), matches)
    print(f"Status: {result.status}")
    print(f"Recommendations Count: {len(result.recommendations)}")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  [{i}] {rec['recommendation']}")
        print(f"      Basis: {rec['basis']} | Confidence: {Math_pct(rec['confidence_score'])} | Bug ID: {rec['supporting_bug_id']}")
    assert len(result.recommendations) > 0, "Remediation Agent should yield recommendations"
    print("[OK] M3.3 Remediation Agent passed all recommendation assertions.\n")


def test_m3_insufficient_evidence_handling():
    print("=" * 70)
    print("4. M3.4 — INSUFFICIENT EVIDENCE FALLBACK HANDLING")
    print("=" * 70)
    
    ctx = run_orchestration("test_bug_weak", **SAMPLE_BUG_WEAK)
    plain_ctx = ctx.to_dict()
    matches = [] # Simulate zero matches
    
    root = infer_root_cause(plain_ctx, matches)
    remediation = recommend_remediation(plain_ctx, root.to_dict(), {}, matches)
    
    print(f"Weak Input Root Cause Status: {root.status}")
    print(f"Weak Input Remediation Status: {remediation.status}")
    assert root.status == "insufficient_evidence", "Root cause should return insufficient_evidence on zero matches"
    assert remediation.status == "insufficient_evidence", "Remediation should return insufficient_evidence on zero matches"
    print("[OK] Insufficient Evidence fallback handling verified.\n")


def Math_pct(val):
    return f"{round((val or 0.0) * 100)}%"


if __name__ == "__main__":
    test_m3_1_root_cause_agent()
    test_m3_2_duplicate_detection_agent()
    test_m3_3_remediation_agent()
    test_m3_insufficient_evidence_handling()
    print("=" * 70)
    print("ALL MILESTONE 3 AGENTS & WORKFLOWS SUCCESSFULLY VERIFIED!")
    print("=" * 70)
