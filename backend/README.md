# BugFix AI - Backend

FastAPI backend for bug submission, historical defect retrieval, and the
deterministic multi-agent diagnosis pipeline.

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows (PowerShell: venv\Scripts\Activate.ps1)
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
copy .env.example .env       # Windows — or: cp .env.example .env
```

## Run the API

```bash
uvicorn app.main:app --reload
```

- API docs (interactive): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Build the Historical Defect Knowledge Base

`../data/raw/` (at the project root, one level up from `backend/`) has
real bug reports sampled from public research datasets — 15 from Eclipse
Platform, 15 from Mozilla Core (via the [logpai/bughub](https://github.com/logpai/bughub)
dataset, based on Lamkanfi et al., MSR'13), and 8 from Apache Hadoop/HDFS
(from public Apache JIRA tickets). Add more by dropping additional CSVs in
here — any column names work, see `app/services/data_cleaning.py` for the
alias mapping.
3. Run:
   ```bash
   python scripts/ingest_knowledge_base.py
   ```
   First run downloads the embedding model (~80MB, needs internet once).
4. Test retrieval:
   ```bash
   python scripts/test_retrieval.py "app crashes when resizing a CSS grid layout"
   ```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/bugs/submit` | Submit a bug report by pasting text — automatically runs Triage + Log Analysis agents (M2.3) |
| POST | `/api/bugs/upload` | Submit a bug report via file upload (.txt/.log/.json) — same automatic analysis |
| GET | `/api/bugs/{id}` | Fetch one submitted bug report, including its `metadata.bug_context` (agent results) |
| GET | `/api/bugs` | List submitted bug reports |
| POST | `/api/knowledge-base/search` | Semantic search over indexed historical bugs |
| GET | `/api/knowledge-base/status` | How many chunks are currently indexed |
| POST | `/api/diagnoses` | Create a persistent diagnosis and run the complete agent pipeline |
| POST | `/api/diagnoses/{session_id}/messages` | Store a follow-up message in a diagnosis session |

## Milestone 3 - Root Cause, Duplicates, and Remediation

The diagnosis endpoint combines Triage and Log Analysis with three structured
retrieval-backed agents:

- **Root Cause Agent** produces a hypothesis, confidence score, reasoning, and supporting historical evidence.
- **Duplicate Detection Agent** ranks semantic matches and classifies them as duplicate, related, or new/unmatched.
- **Remediation Agent** produces actionable recommendations grounded in historical resolution text.

When retrieval evidence is too weak, agents return an explicit insufficient-evidence status instead of presenting speculation as fact.

## Hosted reasoning

Set `LLM_API_KEY` or `OPENROUTER_API_KEY` in `backend/.env` to enable realistic hosted reasoning for
root-cause synthesis, remediation wording, and follow-up questions. The
default provider is OpenRouter with `openai/gpt-4o`; override `LLM_BASE_URL`
and `LLM_MODEL` for another OpenAI-compatible provider. Without a key, the
system uses local evidence-based reasoning and labels hosted reasoning as
unavailable; it does not pretend that a model ran.

## Milestone 2 — Triage & Log Analysis Agents

- **Triage Agent** (`app/services/triage_agent.py`) — classifies severity
  (Critical/High/Medium/Low), priority (P1-P4), and affected component from
  bug text, with a confidence score and a reasoning string built directly
  from which keywords matched. Rule-based on purpose (deterministic,
  testable offline, no API key needed) — see the module docstring for how
  to swap in an LLM-backed version later without changing any caller.
- **Log Analysis Agent** (`app/services/log_analysis_agent.py`) — regex
  parsers for Python, Java, and JavaScript/Node stack traces, extracting
  exception type, message, failure point (file/class/method/line), and the
  ordered call path. Falls back to generic log-line scanning, then to a
  clearly low-confidence "unrecognized" result — never crashes on bad input.
- **Orchestrator** (`app/services/orchestrator.py`) — runs both agents on
  every bug submission automatically, combines them into one `BugContext`,
  and isolates failures so one agent's error/missing input never breaks the
  other or the request.

Run the accuracy validation (M2.4) against real historical data and a
labeled multi-format test set:
```bash
python scripts/validate_agents.py
```
```
This prints a confusion matrix for Triage severity vs. real ground-truth
Priority labels, plus per-case results for the Log Analysis Agent. Current
results: Log Analysis is 100% on its test set; Triage severity is ~50% on
real data — see the script's own printed analysis of why, and the
documented LLM upgrade path in `triage_agent.py`.
