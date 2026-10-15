# Agile Project Documentation

## 1. Project Overview & Vision
**Product Name:** Intelligent Bug Diagnosis Platform (BugFix AI)  
**Vision:** Empower software engineers and DevOps teams to triage, diagnose root causes, detect duplicate defects, and obtain grounded remediation steps within seconds using an autonomous multi-agent pipeline and historical RAG knowledge retrieval.

---

## 2. Agile Framework & Methodology
The project followed an **Agile Scrum** methodology structured across four 2-week Sprints (Milestones 1–4).

### 2.1 Team Roles & Responsibilities
- **Product Owner:** Defines requirements, user personas, acceptance criteria, and manages the product backlog.
- **Scrum Master:** Facilitates daily standups, sprint planning, retrospectives, and removes technical impediments.
- **Full-Stack / AI Engineers:** Implements FastAPI services, multi-agent LLM/RAG pipelines, vector storage (pgvector), and React UI.
- **QA / Validation Engineer:** Authors unit, integration, and E2E regression test suites.

### 2.2 Scrum Ceremonies
- **Sprint Planning:** Bi-weekly breakdown of Epics into estimable User Stories with Story Points (Fibonacci scale: 1, 2, 3, 5, 8).
- **Daily Standups:** 15-minute sync addressing:
  1. What was completed yesterday?
  2. What is committed for today?
  3. Are there any blocking impediments?
- **Sprint Review & Demo:** End-of-sprint demonstration of working software to project mentors/stakeholders.
- **Sprint Retrospective:** Reviewing what went well, what could be improved, and action items for next sprint.

---

## 3. Definitions

### 3.1 Definition of Ready (DoR)
A backlog item is ready for sprint ingestion when:
- User story is clearly articulated in standard format: *As a... I want... So that...*
- Acceptance criteria are clearly defined in Given-When-Then format.
- Dependencies, database schema adjustments, and external API requirements are identified.
- Story has been estimated in story points by the team.

### 3.2 Definition of Done (DoD)
A story is considered complete only when:
- Source code is written, peer-reviewed, and formatted cleanly.
- Unit and integration tests pass with 100% success rate.
- Error handling and fallback mechanisms (e.g. offline deterministic mode when LLM is unavailable) are verified.
- User documentation and API schemas (OpenAPI / Swagger) are updated.
- Feature is merged into the `main` branch.

---

## 4. Epic & Sprint Breakdown

```
├── Epic 1: Data Ingestion & Knowledge Base Foundation (Sprint 1)
├── Epic 2: Core Agent Triage, AST Log Parsing & Authentication (Sprint 2)
├── Epic 3: RAG-Powered Multi-Agent Diagnostic Engine (Sprint 3)
└── Epic 4: Defect Analytics, Self-Improving KB Loop & Production Hardening (Sprint 4)
```

---

### Sprint 1: Knowledge Base Foundation & Data Ingestion (Milestone 1)
**Sprint Goal:** Establish database foundation, parse open-source defect repositories, chunk data, and build vector search retrieval.

| Story ID | User Story | Story Points | Status |
| :--- | :--- | :---: | :---: |
| **US-101** | *As an engineer*, I want to submit bug reports via text paste or file upload (.log, .txt, .json) so that raw defect data is recorded. | 5 | **Done** |
| **US-102** | *As a system*, I want to ingest and sanitize historical defect datasets (Mozilla, Eclipse, Apache) into structured schema. | 8 | **Done** |
| **US-103** | *As a system*, I want to chunk bug reports semantically by stack trace, description, and resolution. | 5 | **Done** |
| **US-104** | *As a system*, I want to embed chunks using `all-MiniLM-L6-v2` and index them in PostgreSQL using `pgvector` for semantic similarity retrieval. | 8 | **Done** |

---

### Sprint 2: Core Agents & Authentication (Milestone 2)
**Sprint Goal:** Build foundational agents (Triage & Log Analysis) and secure user access with JWT authentication.

| Story ID | User Story | Story Points | Status |
| :--- | :--- | :---: | :---: |
| **US-201** | *As a developer*, I want the system to automatically classify defect severity, priority, and affected module. | 5 | **Done** |
| **US-202** | *As a developer*, I want automated stack trace parsing to isolate the exception class, source file, and line number. | 5 | **Done** |
| **US-203** | *As a user*, I want secure user registration, login, and profile persistence using JWT tokens. | 5 | **Done** |
| **US-204** | *As a user*, I want an interactive, modern web chat workspace to interact with diagnostic sessions. | 8 | **Done** |

---

### Sprint 3: Multi-Agent RAG Diagnosis Engine (Milestone 3)
**Sprint Goal:** Develop specialized AI agents for root cause hypothesis, duplicate detection, and remediation planning.

| Story ID | User Story | Story Points | Status |
| :--- | :--- | :---: | :---: |
| **US-301** | *As a triage lead*, I want a Root Cause Agent that correlates bug symptoms against historical defects using RAG and outputs hypotheses with confidence ratings. | 8 | **Done** |
| **US-302** | *As a developer*, I want a Duplicate Detection Agent that evaluates cosine similarity against past defects to identify duplicate or related tickets. | 5 | **Done** |
| **US-303** | *As a developer*, I want a Remediation Agent providing code fix recommendations grounded in past verified resolutions. | 8 | **Done** |
| **US-304** | *As a user*, I want a unified structured findings display in the chat UI with expandable finding cards and evidence citations. | 5 | **Done** |

---

### Sprint 4: Analytics, KB Growth & Final Validation (Milestone 4)
**Sprint Goal:** Implement macroscopic defect analytics, continuous knowledge base learning loop, and end-to-end integration validation.

| Story ID | User Story | Story Points | Status |
| :--- | :--- | :---: | :---: |
| **US-401** | *As an engineering manager*, I want a Defect Pattern Analytics dashboard showing severity distribution, component hotspots, and recurring error themes. | 8 | **Done** |
| **US-402** | *As a user*, I want to filter analytics charts by component, severity level, and date ranges. | 5 | **Done** |
| **US-403** | *As a developer*, I want to mark diagnosed bugs as 'Resolved' and index confirmed fixes back into the vector store to continuously improve future recommendations. | 8 | **Done** |
| **US-404** | *As a QA engineer*, I want an end-to-end test suite and validation scripts testing multi-language bugs, agent resilience, and performance timing. | 5 | **Done** |

---

## 5. Agile Metrics & Velocity

- **Average Sprint Velocity:** ~26 Story Points per sprint.
- **Sprint Commitment vs. Completed:**
  - Sprint 1: 26 / 26 SP (100%)
  - Sprint 2: 23 / 23 SP (100%)
  - Sprint 3: 26 / 26 SP (100%)
  - Sprint 4: 26 / 26 SP (100%)
- **Defect Leakage:** 0 critical regressions in production release branch.

---

## 6. Sprint Retrospective Summary

### What Went Well
- Modular architecture with clear agent boundaries allowed independent testing and deterministic fallback modes.
- pgvector semantic search provided sub-100ms vector lookups for historical context.
- Fast, clean React interface with real-time job status polling provides high UX responsiveness.

### Areas for Improvement & Action Items
- LLM inference latency varies with third-party providers; resolved by implementing payload trimming and robust fallback agents.
- Heavy embedding model loading during integration testing resolved by using session-scoped warm-up fixtures.
