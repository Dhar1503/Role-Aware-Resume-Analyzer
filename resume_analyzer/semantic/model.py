"""
Sentence-embedding model (bge-small-en-v1.5, ~130 MB, CPU).

Loaded lazily and once per process: the first call pays ~1-2 s (or a one-off
download), later calls are milliseconds. Everything degrades gracefully when
the model or its dependencies are missing - the rest of the analysis still
runs and JD fit simply reports that it is unavailable.

bge was chosen over all-MiniLM-L6-v2 because a single threshold separates real
matches from unrelated text across the validation set; MiniLM's ranges overlap.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Sequence
from functools import lru_cache

MODEL_NAME = os.environ.get("RESUME_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def get_model():
    """The shared SentenceTransformer, or None when unavailable."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        with _LOCK:
            return SentenceTransformer(MODEL_NAME, device="cpu")
    except Exception:       # no local cache and no network, corrupt download, ...
        return None


def available() -> bool:
    return get_model() is not None


def embed(texts: Sequence[str], as_queries: bool = False):
    """L2-normalised embeddings, or None when the model is unavailable."""
    model = get_model()
    if model is None or not texts:
        return None
    prepared: list[str] = [QUERY_PREFIX + t for t in texts] if as_queries else list(texts)
    return model.encode(prepared, batch_size=32, normalize_embeddings=True, show_progress_bar=False)


def warm_up() -> bool:
    """Load both models now, so no visitor's request pays for the import.

    spaCy's NER backend pulls in torch on its first call (about seven seconds),
    which otherwise lands on whichever upload first needs the name fallback.
    """
    from ..extraction import nlp
    nlp.entities("Priya Sharma worked at Acme Labs in Bengaluru.", "PERSON")
    return available()
