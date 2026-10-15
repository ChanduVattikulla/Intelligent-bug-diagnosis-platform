# 🐞 Intelligent Bug Diagnosis Platform (BugFix AI)

An AI-driven multi-agent platform designed to automate defect triage, perform AST-level log and stack trace analysis, hypothesize root causes via RAG (Retrieval-Augmented Generation) against historical defect databases, identify duplicate issues, provide grounded remediation recommendations, and track defect patterns through real-time analytics.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![React: 18](https://img.shields.io/badge/React-18.x-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)

---

## 📖 Table of Contents
- [Architecture & Multi-Agent Pipeline](#-architecture--multi-agent-pipeline)
- [Key Features](#-key-features)
- [Agile Documentation & Sprints](#-agile-documentation--sprints)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Local Development Setup](#-local-development-setup)
- [Deployment Guide](#-deployment-guide)
- [License](#-license)

---

## 🧠 Architecture & Multi-Agent Pipeline

The platform uses an orchestrated pipeline of specialized agents:

```
[ Developer Bug Submission (Text / File / Logs) ]
                       │
                       ▼
         ┌───────────────────────────┐
         │       Triage Agent        │  ──► Severity, Component & Priority
         └─────────────┬─────────────┘
                       ▼
         ┌───────────────────────────┐
         │     Log Analysis Agent    │  ──► AST Trace Extraction & Exception Isolation
         └─────────────┬─────────────┘
                       ▼
         ┌───────────────────────────┐
         │ Historical RAG Retrieval  │  ──► Semantic Search across pgvector Defect Chunks
         └─────────────┬─────────────┘
                       ▼
    ┌──────────────────┴──────────────────┐
    ▼                                     ▼
┌────────────────────────┐   ┌───────────────────────────┐
│    Root Cause Agent    │   │ Duplicate Detection Agent │
└───────────┬────────────┘   └─────────────┬─────────────┘
            └──────────────┬───────────────┘
                           ▼
              ┌─────────────────────────┐
              │    Remediation Agent    │  ──► Code Fix Recommendations
              └────────────┬────────────┘
                           ▼
       [ Unified Diagnostic Findings & Live Chat ]
                           │
                           ▼
           (Self-Improving Feedback Loop)
         [ "Mark as Resolved" ➔ KB Indexing ]
```

---

## ✨ Key Features

1. **Bug Submission Engine (M1):** Direct text submission or multi-format file uploads (`.log`, `.txt`, `.json`) with automatic sanitization and chunking.
2. **PostgreSQL & pgvector RAG (M1):** Semantic search backed by `sentence-transformers/all-MiniLM-L6-v2` embeddings over open-source defect repositories (Mozilla, Apache, Eclipse).
3. **Automated Triage & Log Analysis (M2):** Rapid classification of severity/priority and automated stack trace parsing.
4. **JWT Authentication & Session Management (M2):** Secure user management with authentication, session recovery, and diagnosis history.
5. **Specialized Diagnostic Agents (M3):**
   - **Root Cause Agent:** Generates hypotheses with confidence scoring and historical citations.
   - **Duplicate Detection Agent:** Identifies duplicate and related defects using cosine similarity.
   - **Remediation Agent:** Generates actionable code fixes grounded in verified historical resolutions.
6. **Defect Pattern Analytics (M4):** Interactive charts (powered by Recharts) showing severity distributions, component frequency hotspots, and timeline trends.
7. **Knowledge Base Growth Mechanism (M4):** Close the feedback loop by marking bugs as resolved to index verified fixes back into the vector store.

---

## 📋 Agile Documentation & Sprints

Complete Agile Scrum documentation detailing user stories, story points, acceptance criteria, definition of done, and sprint velocities is available in:
👉 **[docs/AGILE.md](docs/AGILE.md)**

Milestone project summaries and validation reports:
👉 **[docs/Milestone4_Report.md](docs/Milestone4_Report.md)**

---

## 🛠 Tech Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic, PyJWT
- **AI & RAG:** SentenceTransformers (`all-MiniLM-L6-v2`), OpenRouter / LLM fallback reasoning
- **Database:** PostgreSQL with `pgvector` extension (Neon DB / Supabase compatible)
- **Frontend:** React 18, Recharts, CSS3 (Modern Responsive Dark Theme)
- **Testing:** Pytest, FastAPI TestClient

---

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # Triage, Log Analysis, Root Cause, Duplicate, Remediation
│   │   ├── orchestration/   # Multi-agent orchestrator pipeline
│   │   ├── routers/         # API routes (auth, bug_submission, diagnosis, knowledge_base, analytics)
│   │   ├── services/        # Embeddings, Vector store, LLM service, Chunking
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── db_models.py
│   │   └── main.py
│   ├── scripts/             # Ingestion and validation scripts
│   ├── tests/               # Unit, integration, and E2E test suites
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Sidebar, ChatArea, MessageBubble, Icons)
│   │   ├── contexts/        # Auth context
│   │   ├── pages/           # ChatPage, AnalyticsPage, HistoryPage, Auth pages
│   │   └── utils/           # API clients, local storage, diagnostic runners
│   └── package.json
├── docs/
│   ├── AGILE.md             # Complete Agile Scrum documentation & stories
│   └── Milestone4_Report.md # Milestone 4 validation and project report
├── LICENSE                  # MIT License
└── README.md
```

---

## 💻 Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/ChanduVattikulla/Intelligent-bug-diagnosis-platform.git
cd Intelligent-bug-diagnosis-platform
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>?sslmode=require
JWT_SECRET=your_secret_key_here
FRONTEND_ORIGIN=http://localhost:3000
LLM_API_KEY=your_openrouter_api_key
LLM_MODEL=openrouter/free
```

Start the backend server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm start
```
The application will be accessible at `http://localhost:3000`.

---

## 🚀 Deployment Guide

Detailed deployment instructions for live hosting:
- **Backend:** Render / Railway / Fly.io (Python FastAPI Web Service)
- **Database:** Neon PostgreSQL with `pgvector`
- **Frontend:** Vercel / Netlify (React Static Site with API proxy)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
