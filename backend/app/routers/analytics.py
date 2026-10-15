from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.db_session import get_session
from app.db_models import BugSubmission, DiagnosisSession, DefectChunk

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/defects")
def get_defect_analytics(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    session = get_session()
    try:
        # Build base filters for BugSubmission
        bug_filters = []
        if date_from:
            bug_filters.append(BugSubmission.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            bug_filters.append(BugSubmission.created_at <= datetime.fromisoformat(date_to))
        
        # Get matching bugs and their diagnosis sessions
        query = select(BugSubmission, DiagnosisSession).outerjoin(
            DiagnosisSession, BugSubmission.id == DiagnosisSession.bug_id
        )
        if bug_filters:
            query = query.where(and_(*bug_filters))
            
        records = session.execute(query).all()

        total_bugs = 0
        severity_dist = {}
        component_dist = {}
        exception_dist = {}
        root_cause_dist = {}
        duplicate_count = 0
        remediation_supported_count = 0
        bug_freq_over_time = {}

        for bug, diag in records:
            # We do some filtering in Python since JSONB filtering can be complex
            diag_state = diag.state if diag and diag.state else {}
            
            triage = diag_state.get("triage", {})
            log_analysis = diag_state.get("logAnalysis", {})
            root_cause = diag_state.get("rootCause", {})
            duplicate = diag_state.get("duplicateDetection", {})
            remediation = diag_state.get("remediation", {})

            bug_component = triage.get("component") or "Unknown"
            bug_severity = triage.get("severity") or "Unknown"
            bug_exception = log_analysis.get("exception_type") or "Unknown"

            if component and component.lower() not in bug_component.lower():
                continue
            if severity and severity.lower() != bug_severity.lower():
                continue
            if exception_type and exception_type.lower() not in bug_exception.lower():
                continue

            total_bugs += 1

            severity_dist[bug_severity] = severity_dist.get(bug_severity, 0) + 1
            component_dist[bug_component] = component_dist.get(bug_component, 0) + 1
            exception_dist[bug_exception] = exception_dist.get(bug_exception, 0) + 1

            if rc_hypothesis := root_cause.get("hypothesis"):
                # Simplistic theming by taking first few words, or just use the hypothesis text
                theme = rc_hypothesis.split(".")[0][:50] + ("..." if len(rc_hypothesis.split(".")[0]) > 50 else "")
                root_cause_dist[theme] = root_cause_dist.get(theme, 0) + 1
            
            if duplicate.get("status") == "potential_duplicate":
                duplicate_count += 1
                
            if remediation.get("status") == "supported":
                remediation_supported_count += 1

            day_str = bug.created_at.strftime("%Y-%m-%d") if bug.created_at else "Unknown"
            bug_freq_over_time[day_str] = bug_freq_over_time.get(day_str, 0) + 1

        top_recurring_components = sorted([{"component": k, "count": v} for k, v in component_dist.items()], key=lambda x: x["count"], reverse=True)[:5]
        common_error_patterns = sorted([{"exception_type": k, "count": v} for k, v in exception_dist.items()], key=lambda x: x["count"], reverse=True)[:5]
        
        kb_size = session.scalar(select(func.count(DefectChunk.chunk_id))) or 0

        return {
            "total_bugs": total_bugs,
            "severity_distribution": severity_dist,
            "component_distribution": component_dist,
            "exception_type_distribution": exception_dist,
            "root_cause_distribution": root_cause_dist,
            "duplicate_rate": (duplicate_count / total_bugs * 100) if total_bugs > 0 else 0.0,
            "bug_frequency_over_time": [{"date": k, "count": v} for k, v in sorted(bug_freq_over_time.items())],
            "top_recurring_components": [c["component"] for c in top_recurring_components],
            "common_error_patterns": [e["exception_type"] for e in common_error_patterns],
            "knowledge_base_size": kb_size,
            "remediation_supported_rate": (remediation_supported_count / total_bugs * 100) if total_bugs > 0 else 0.0,
        }
    finally:
        session.close()
