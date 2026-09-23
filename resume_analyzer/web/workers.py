"""
Guard against a multi-worker deployment.

Analysis results live in this process's memory (see ``store.py``). With more
than one worker, a visitor is load-balanced to a worker that has never seen
their result and gets "that result has expired" at random - a failure that
looks like a bug in the analyser and is painful to reproduce.

Nothing in Flask or gunicorn tells the app how many workers exist, so this
reads the usual configuration sources and complains loudly at start-up.
Set ``STRICT_SINGLE_WORKER=1`` to make it fatal instead (recommended for a
real deployment, where a silent misconfiguration is worse than a failed boot).
"""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_ENV_COUNTS = ("WEB_CONCURRENCY", "GUNICORN_WORKERS", "UVICORN_WORKERS", "WORKERS", "NUM_WORKERS")
_FLAG = re.compile(r"(?:^|\s)(?:-w|--workers(?:=|\s+))\s*(\d+)")

MESSAGE = (
    "Configured for {count} workers, but analysis results are stored in the worker's own memory. "
    "Visitors will randomly be told their report expired. Run a single worker "
    "(gunicorn -w 1), or move the result store to Redis before scaling out."
)


def _from_env() -> List[Tuple[str, int]]:
    found = []
    for name in _ENV_COUNTS:
        raw = os.environ.get(name, "").strip()
        if raw.isdigit():
            found.append((name, int(raw)))
    for name in ("GUNICORN_CMD_ARGS", "GUNICORN_OPTS"):
        match = _FLAG.search(os.environ.get(name, ""))
        if match:
            found.append((name, int(match.group(1))))
    return found


def _from_argv(argv: Optional[List[str]] = None) -> List[Tuple[str, int]]:
    match = _FLAG.search(" ".join(argv if argv is not None else sys.argv))
    return [("command line", int(match.group(1)))] if match else []


def detect_worker_count(argv: Optional[List[str]] = None) -> Optional[Tuple[str, int]]:
    """The configured worker count and where it came from, or None if nothing says."""
    found = _from_env() + _from_argv(argv)
    return max(found, key=lambda item: item[1]) if found else None


def check_single_worker(argv: Optional[List[str]] = None, strict: Optional[bool] = None) -> Optional[str]:
    """Warn (or raise) when the deployment asks for more than one worker."""
    detected = detect_worker_count(argv)
    if not detected or detected[1] <= 1:
        return None
    source, count = detected
    message = MESSAGE.format(count=count) + f" [{source}]"
    if strict if strict is not None else os.environ.get("STRICT_SINGLE_WORKER") == "1":
        raise RuntimeError(message)
    logger.warning(message)
    print(f"WARNING: {message}", file=sys.stderr, flush=True)
    return message
