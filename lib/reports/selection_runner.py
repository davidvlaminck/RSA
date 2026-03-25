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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _preflight_check_mappings(report_names: list[str], settings: dict) -> None:
    """Warn if any report references a spreadsheet_id that cannot be resolved to a local workbook.

    - Scans the Reports/<report>.py file for `spreadsheet_id = '...'` if present.
    - Uses outputs.spreadsheet_map.lookup to resolve spreadsheet ids or falls back to checking
      if filename exists in configured output directory.
    - Logs warnings but does not abort the run.
    """
    try:
        from outputs.spreadsheet_map import lookup
    except Exception:
        logger.debug('spreadsheet_map not available; skipping mapping preflight')
        return

    output_dir = settings.get('output', {}).get('excel', {}).get('output_dir') or 'RSA_OneDrive'
    out_path = Path(output_dir)

    reports_dir = Path(__file__).resolve().parents[2] / 'Reports'
    msgs = []
    for rname in report_names:
        # expect rname like 'Report0002' -> file Reports/Report0002.py
        rfile = reports_dir / f"{rname}.py"
        if not rfile.exists():
            continue
        try:
            txt = rfile.read_text(encoding='utf-8')
        except Exception:
            continue
        # look for spreadsheet_id attribute
        import re
        m = re.search(r"spreadsheet_id\s*=\s*['\"](?P<id>[^'\"]+)['\"]", txt)
        if not m:
            continue
        sid = m.group('id').strip()
        if not sid:
            continue
        mapped = lookup(sid)
        if mapped:
            candidate = (out_path / mapped)
            if not candidate.exists():
                msg = f"Report {rname} maps spreadsheet id {sid} -> {mapped} but file not found at {candidate}"
                msgs.append(msg)
        else:
            # if not mapped, warn and show fallback path
            candidate = out_path / (sid + '.xlsx')
            msg = f"Report {rname} references spreadsheet id {sid} but no mapping found. Fallback file would be: {candidate}"
            msgs.append(msg)
    # emit collected warnings once so they're visible even when logger isn't configured
    if msgs:
        header = f"Spreadsheet mapping preflight: {len(msgs)} potential issues found"
        try:
            logger.warning(header)
            for m in msgs:
                logger.warning(m)
        except Exception:
            # fallback to printing to stdout/stderr so the user sees it
            print(header)
            for m in msgs:
                print(m)


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
    # preflight: warn about unresolved spreadsheet ids for the selected reports
    _preflight_check_mappings(report_names, settings)
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
