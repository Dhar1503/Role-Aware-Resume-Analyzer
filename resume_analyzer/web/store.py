"""
Short-lived, in-memory store for analysis results.

Resumes carry personal data, so nothing is written to disk and nothing is kept
for long:

* keys are unguessable (``secrets.token_urlsafe``), never sequential, so a
  result URL cannot be walked or found by counting;
* entries expire (default one hour) and expired ones are dropped on every
  access, not only when someone asks for them;
* the store is capped, so a busy demo evicts the oldest entries instead of
  growing until the process dies;
* anyone can delete their own result immediately from the results page.

A process restart clears everything, which is the right default for a public
demo. A multi-process deployment would need shared storage - and that is a
reason to keep this deployment single-process (see the README).
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

DEFAULT_TTL_SECONDS = 3600
DEFAULT_MAX_ENTRIES = 200
KEY_BYTES = 24                      # ~32 characters of base64url


@dataclass
class _Entry:
    value: Any
    expires_at: float


class ResultStore:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS, max_entries: int = DEFAULT_MAX_ENTRIES):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self._lock = threading.Lock()

    def put(self, value: Any) -> str:
        key = secrets.token_urlsafe(KEY_BYTES)
        with self._lock:
            self._purge()
            while len(self._entries) >= self.max_entries:
                oldest = min(self._entries, key=lambda k: self._entries[k].expires_at)
                del self._entries[oldest]
            self._entries[key] = _Entry(value, time.time() + self.ttl_seconds)
        return key

    def get(self, key: str) -> Any | None:
        with self._lock:
            self._purge()
            entry = self._entries.get(key)
            return entry.value if entry else None

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._entries.pop(key, None) is not None

    def expires_in(self, key: str) -> int | None:
        with self._lock:
            entry = self._entries.get(key)
            return max(0, int(entry.expires_at - time.time())) if entry else None

    def _purge(self) -> None:
        now = time.time()
        for key in [k for k, e in self._entries.items() if e.expires_at <= now]:
            del self._entries[key]

    def __len__(self) -> int:
        with self._lock:
            self._purge()
            return len(self._entries)
