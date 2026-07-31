from __future__ import annotations

import contextlib
import io
import subprocess

from lib.reports import pipeline_runner


class _FakeWorkerProcess:
    returncode = 0

    def __init__(self, output: str = "worker line 1\nworker line 2\n"):
        self.output = output
        self.killed = False

    def communicate(self, timeout: int | None = None):
        return self.output, ""

    def kill(self):
        self.killed = True


def test_streamed_worker_output_is_written_to_python_stdout(monkeypatch):
    monkeypatch.setattr(
        pipeline_runner,
        "group_reports_by_datasource",
        lambda reports: {"ArangoDB": reports},
    )

    fake_process = _FakeWorkerProcess()

    def fake_popen(cmd, stdout=None, stderr=None, text=False, errors=None):
        assert cmd[:3] == [__import__("sys").executable, "-m", "lib.reports.worker"]
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.STDOUT
        assert text is True
        assert errors == "replace"
        return fake_process

    monkeypatch.setattr(pipeline_runner.subprocess, "Popen", fake_popen)

    captured = io.StringIO()
    settings = {"report_execution": {"max_concurrent": 1, "timeout_seconds": 10}}

    with contextlib.redirect_stdout(captured):
        return_code, failed = pipeline_runner.run_pipelines_by_datasource(
            ["Report0002"],
            settings,
            "settings.json",
            stream_output=True,
        )

    assert return_code == 0
    assert failed == []
    assert captured.getvalue() == "worker line 1\nworker line 2\n"


def test_streamed_worker_timeout_is_reported_and_process_is_killed(monkeypatch):
    monkeypatch.setattr(
        pipeline_runner,
        "group_reports_by_datasource",
        lambda reports: {"ArangoDB": reports},
    )

    fake_process = _FakeWorkerProcess()
    monkeypatch.setattr(
        pipeline_runner.subprocess,
        "Popen",
        lambda *args, **kwargs: fake_process,
    )
    monkeypatch.setattr(
        fake_process,
        "communicate",
        lambda timeout=None: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd=[], timeout=timeout)),
    )

    settings = {"report_execution": {"max_concurrent": 1, "timeout_seconds": 10}}
    return_code, failed = pipeline_runner.run_pipelines_by_datasource(
        ["Report0002"],
        settings,
        "settings.json",
        stream_output=True,
    )

    assert return_code == 1
    assert failed == ["Report0002"]
    assert fake_process.killed is True
