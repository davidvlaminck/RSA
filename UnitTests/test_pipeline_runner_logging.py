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
        self._lines = output.splitlines(keepends=True)
        self._idx = 0

    def poll(self):
        return self.returncode

    def readline(self):
        if self._idx < len(self._lines):
            line = self._lines[self._idx]
            self._idx += 1
            return line
        return ""

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
    settings = {"report_execution": {"max_concurrent": 1, "query_timeout_seconds": 60}}

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


def test_failed_worker_process_returns_failed_reports(monkeypatch):
    monkeypatch.setattr(
        pipeline_runner,
        "group_reports_by_datasource",
        lambda reports: {"ArangoDB": reports},
    )

    fake_process = _FakeWorkerProcess()
    fake_process.returncode = 1

    def fake_popen(cmd, stdout=None, stderr=None, text=False, errors=None):
        return fake_process

    monkeypatch.setattr(pipeline_runner.subprocess, "Popen", fake_popen)

    settings = {"report_execution": {"max_concurrent": 1, "query_timeout_seconds": 60}}
    return_code, failed = pipeline_runner.run_pipelines_by_datasource(
        ["Report0002"],
        settings,
        "settings.json",
        stream_output=True,
    )

    assert return_code == 1
    assert failed == ["Report0002"]
