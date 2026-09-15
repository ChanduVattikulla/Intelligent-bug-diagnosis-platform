# backend/app/config.py
"""Central place for all settings, loaded from environment variables (.env)."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present. Never crashes if it's missing — defaults kick in.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

DATABASE_URL = os.getenv("DATABASE_URL", "")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
JWT_SECRET = os.getenv("JWT_SECRET", "bugfix-ai-secure-jwt-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "30"))

# Optional OpenAI-compatible hosted model. When absent, the deterministic
# offline agents remain available and reports label that mode explicitly.
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "openrouter/free")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

RAW_DATA_DIR = BASE_DIR.parent / "data" / "raw"

# Caps how many rows are read from each CSV in data/raw/ per ingestion run —
# without this, a 50,000-row research dataset would take a very long time to
# embed on a first pass and can look like the script has hung. Raise this
# (or set MAX_ROWS_PER_FILE in .env) once you've confirmed a dataset's
# columns map correctly and you're ready to index it in full.
MAX_ROWS_PER_FILE = int(os.getenv("MAX_ROWS_PER_FILE", "500"))

# Chunking parameters — how long-form text (descriptions, stack traces,
# comments, resolutions) gets split before embedding. See app/services/chunking.py.
CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP_CHARS = 120

# Only these file types are accepted for bug report / log uploads.
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".log", ".json"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
