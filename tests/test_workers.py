"""The single-worker guard: results live in one process, so more workers break them."""

import pytest

from resume_analyzer.web import create_app
from resume_analyzer.web.workers import check_single_worker, detect_worker_count


@pytest.mark.parametrize("env, expected", [
    ({"WEB_CONCURRENCY": "4"}, 4),
    ({"GUNICORN_WORKERS": "2"}, 2),
    ({"GUNICORN_CMD_ARGS": "--workers 8 --timeout 120"}, 8),
    ({"GUNICORN_CMD_ARGS": "-w 3"}, 3),
    ({"WEB_CONCURRENCY": "1"}, 1),
    ({}, None),
    ({"WEB_CONCURRENCY": "not-a-number"}, None),
])
def test_detects_worker_count_from_the_environment(monkeypatch, env, expected):
    for name in ("WEB_CONCURRENCY", "GUNICORN_WORKERS", "GUNICORN_CMD_ARGS", "UVICORN_WORKERS",
                 "WORKERS", "NUM_WORKERS", "GUNICORN_OPTS"):
        monkeypatch.delenv(name, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    detected = detect_worker_count(argv=[])
    assert (detected[1] if detected else None) == expected


def test_detects_workers_on_the_command_line():
    assert detect_worker_count(argv=["gunicorn", "-w", "4", "app:app"])[1] == 4
    assert detect_worker_count(argv=["gunicorn", "--workers=6", "app:app"])[1] == 6


def test_single_worker_is_silent(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    assert check_single_worker(argv=[]) is None


def test_multiple_workers_warn(monkeypatch, capsys):
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    message = check_single_worker(argv=[], strict=False)
    assert "4 workers" in message and "expired" in message
    assert "WARNING" in capsys.readouterr().err


def test_strict_mode_refuses_to_start(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    with pytest.raises(RuntimeError, match="4 workers"):
        check_single_worker(argv=[], strict=True)


def test_health_endpoint_reports_the_warning(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        health = client.get("/healthz").get_json()
    assert health["worker_warning"] and "3 workers" in health["worker_warning"]


def test_health_endpoint_is_quiet_when_correctly_configured(monkeypatch):
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        assert client.get("/healthz").get_json()["worker_warning"] is None
