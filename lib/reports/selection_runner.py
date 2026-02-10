"""Shared runner for executing a selected list of reports.

Used by:
- run_single_report.py (single report)
- main_selection_list.py (small selection)
- ReportLoopRunner.run_selected (optional)
"""
from __future__ import annotations

from SettingsManager import SettingsManager
from lib.reports.ReportLoopRunner import ReportLoopRunner
from lib.reports.pipeline_runner import run_pipelines_by_datasource


def run_selection(
    settings_path: str,
    report_names: list[str],
    *,
    force_parallel: bool | None = None,
    stream_output: bool = True,
) -> int:
    """Run a list of reports with shared logic.

    - Uses sequential in-process execution by default.
    - Uses pipeline-parallel execution if configured or forced.

    Returns 0 on success, 1 on failure.
    """
    settings = SettingsManager(settings_path=settings_path).settings
    exec_cfg = settings.get("report_execution", {})
    mode = exec_cfg.get("mode", "sequential")

    use_parallel = force_parallel if force_parallel is not None else mode == "parallel_by_datasource"

    if use_parallel:
        return run_pipelines_by_datasource(
            report_names,
            settings,
            settings_path,
            stream_output=stream_output,
        )

    # Sequential: reuse ReportLoopRunner logic for consistent behavior
    runner = ReportLoopRunner(settings_path=settings_path)
    runner.run_selected(report_names)
    return 0
