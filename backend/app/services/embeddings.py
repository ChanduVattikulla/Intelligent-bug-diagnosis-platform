# backend/app/services/embeddings.py
"""
Generates embeddings using a local sentence-transformers model.

Why a local model instead of an API (OpenAI/etc.):
  - No API key or per-call cost while iterating on the pipeline.
  - Fully reproducible/offline once the model is cached locally.
  - 'all-MiniLM-L6-v2' is small (~80MB), fast on CPU, and a common baseline
    for semantic search — good enough for this milestone. Swappable later
    via EMBEDDING_MODEL_NAME in .env if a bigger model is needed.

Note: the model is downloaded from Hugging Face the first time this runs,
so that first run needs internet access. After that it's cached locally
(usually under ~/.cache/huggingface) and works offline.
"""

from functools import lru_cache
from typing import List

from app.config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the rest of the app can start up even before this
    # dependency's first (potentially slow) model download completes.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embeds a batch of texts. Returns one vector (list of floats) per text."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
