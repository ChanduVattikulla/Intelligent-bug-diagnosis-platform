# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app import database
from app.routers import auth, bug_submission, diagnosis, knowledge_base


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
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
