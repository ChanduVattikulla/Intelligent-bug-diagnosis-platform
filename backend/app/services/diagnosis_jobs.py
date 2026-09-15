"""Diagnosis jobs worker and state tracking, supporting DB persistence with in-memory fallback."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from app.db_models import DiagnosisJob
from app.db_session import get_session

_executor = ThreadPoolExecutor(max_workers=4)
_in_memory_jobs = {}
_lock = Lock()


def _now():
    return datetime.now(timezone.utc)


def create_job(worker, *args):
    job_id = f"job_{uuid4().hex[:12]}"
    now_iso = _now().isoformat()

    with _lock:
        _in_memory_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "active_agent": None,
            "stages": [],
            "result": None,
            "error": None,
            "updated_at": now_iso,
        }

    try:
        session = get_session()
        try:
            session.add(DiagnosisJob(id=job_id, status="queued", stages=[], updated_at=_now()))
            session.commit()
        finally:
            session.close()
    except Exception:
        pass  # Fallback to in-memory if DB session unavailable

    _executor.submit(worker, job_id, *args)
    return job_id


def update_job(job_id: str, agent: str, status: str):
    now_iso = _now().isoformat()
    with _lock:
        mem_job = _in_memory_jobs.get(job_id)
        if mem_job:
            mem_job["status"] = "running" if status == "working" else mem_job["status"]
            mem_job["active_agent"] = agent if status == "working" else None
            stages = mem_job["stages"]
            existing = next((stage for stage in stages if stage["agent"] == agent), None)
            if existing:
                existing["status"] = status
            else:
                stages.append({"agent": agent, "status": status})
            mem_job["updated_at"] = now_iso

    try:
        session = get_session()
        try:
            job = session.get(DiagnosisJob, job_id)
            if job:
                db_stages = list(job.stages or [])
                existing = next((stage for stage in db_stages if stage["agent"] == agent), None)
                if existing:
                    existing["status"] = status
                else:
                    db_stages.append({"agent": agent, "status": status})
                job.stages = db_stages
                job.status = "running" if status == "working" else job.status
                job.active_agent = agent if status == "working" else None
                job.updated_at = _now()
                session.commit()
        finally:
            session.close()
    except Exception:
        pass


def finish_job(job_id: str, result=None, error=None):
    now_iso = _now().isoformat()
    with _lock:
        mem_job = _in_memory_jobs.get(job_id)
        if mem_job:
            mem_job["status"] = "failed" if error else "completed"
            mem_job["active_agent"] = None
            mem_job["result"] = result
            mem_job["error"] = error
            mem_job["updated_at"] = now_iso

    try:
        session = get_session()
        try:
            job = session.get(DiagnosisJob, job_id)
            if job:
                job.status = "failed" if error else "completed"
                job.active_agent = None
                job.result = result
                job.error = error
                job.updated_at = _now()
                session.commit()
        finally:
            session.close()
    except Exception:
        pass


def get_job(job_id: str):
    try:
        session = get_session()
        try:
            job = session.get(DiagnosisJob, job_id)
            if job:
                return {
                    "job_id": job.id,
                    "status": job.status,
                    "active_agent": job.active_agent,
                    "stages": job.stages or [],
                    "result": job.result,
                    "error": job.error,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else "",
                }
        finally:
            session.close()
    except Exception:
        pass

    with _lock:
        mem_job = _in_memory_jobs.get(job_id)
        return dict(mem_job) if mem_job else None