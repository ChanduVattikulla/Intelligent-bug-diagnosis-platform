# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app import database
from app.routers import auth, bug_submission, diagnosis, knowledge_base, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="BugFix AI — Backend",
    description="Bug submission, historical defect retrieval, and multi-agent diagnosis pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip() and o.strip() != "*"]
if "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if FRONTEND_ORIGIN != "*" else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True if FRONTEND_ORIGIN != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(bug_submission.router)
app.include_router(knowledge_base.router)
app.include_router(diagnosis.router)
app.include_router(analytics.router)
