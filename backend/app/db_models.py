"""SQLAlchemy models for the PostgreSQL application database."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    provider_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class BugSubmission(Base):
    __tablename__ = "bug_submissions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    logs: Mapped[str | None] = mapped_column(Text)
    uploaded_file_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="submitted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class DiagnosisSession(Base):
    __tablename__ = "diagnosis_sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bug_id: Mapped[str] = mapped_column(String(255), ForeignKey("bug_submissions.id"), nullable=False)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    diagnosis_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("diagnosis_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

class DiagnosisJob(Base):
    __tablename__ = "diagnosis_jobs"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    active_agent: Mapped[str | None] = mapped_column(String(100))
    stages: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class HistoricalDefect(Base):
    __tablename__ = "historical_defects"

    bug_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    component: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(255))


class DefectChunk(Base):
    __tablename__ = "defect_chunks"

    chunk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    historical_bug_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("historical_defects.bug_id"), nullable=False
    )
    chunk_type: Mapped[str | None] = mapped_column(String(100))
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    chunk_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)