# backend/scripts/validate_milestone4.py
import sys
import time
import requests

API_BASE = "http://127.0.0.1:8000/api"

print("="*60)
print(" Milestone 4 Validation Script (E2E Tests)")
print("="*60)
print()

# 1. Test Analytics Endpoint
print("Running Check 1: Analytics Endpoint Schema")
try:
    res = requests.get(f"{API_BASE}/analytics/defects")
    res.raise_for_status()
    data = res.json()
    expected_keys = [
        "total_bugs", "severity_distribution", "component_distribution",
        "exception_type_distribution", "root_cause_distribution", "duplicate_rate",
        "bug_frequency_over_time", "top_recurring_components",
        "common_error_patterns", "knowledge_base_size", "remediation_supported_rate"
    ]
    missing = [k for k in expected_keys if k not in data]
    if missing:
        print(f"[FAIL] Missing analytics keys: {missing}")
    else:
        print("[PASS] Analytics endpoint returned correct schema.")
except Exception as e:
    print(f"[FAIL] Analytics endpoint failed: {e}")

print()

# 2. Test KB Resolution
print("Running Check 2: Knowledge Base Growth (Resolve)")
try:
    bug_payload = {
        "title": "DB Connection Refused in Validator",
        "description": "App cannot start up",
        "stack_trace": "ConnectionRefusedError: [Errno 111] Connection refused\n  at db_connect (db.py:44)",
        "error_log": ""
    }
    submit_res = requests.post(f"{API_BASE}/diagnoses/start", json=bug_payload)
    submit_res.raise_for_status()
    job_id = submit_res.json()["job_id"]
    
    session_id = None
    start = time.time()
    while time.time() - start < 60:
        job_res = requests.get(f"{API_BASE}/diagnoses/jobs/{job_id}")
        jdata = job_res.json()
        if jdata["status"] == "completed":
            session_id = jdata["result"]["session_id"]
            break
        elif jdata["status"] == "failed":
            print(f"[FAIL] Bug diagnosis failed: {jdata.get('error')}")
            break
        time.sleep(1)
        
    if session_id:
        resolve_payload = {
            "session_id": session_id,
            "confirmed_fix": "Increased connection timeout and added retry loop.",
            "root_cause_summary": "DB container was taking too long to start before app container.",
            "affected_component": "Database"
        }
        res_req = requests.post(f"{API_BASE}/knowledge-base/resolve", json=resolve_payload)
        rdata = res_req.json()
        if res_req.status_code == 200 and rdata.get("status") in ["indexed", "already_indexed"]:
            print(f"[PASS] Successfully resolved and indexed bug into KB.")
        else:
            print(f"[FAIL] Resolve endpoint returned unexpected status: {res_req.status_code} - {rdata}")
    else:
        print("[FAIL] Could not get session_id to test resolution.")
except Exception as e:
    print(f"[FAIL] Knowledge base growth failed: {e}")

print()
print("="*60)
print(" Milestone 4 Validation Complete ")
print("="*60)
