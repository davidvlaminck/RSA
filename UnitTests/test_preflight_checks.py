import json
import pytest
from unittest.mock import MagicMock

from lib.reports.ReportLoopRunner import ReportLoopRunner


def test_preflight_checks_success(monkeypatch, tmp_path):
    settings = {
        'databases': {
            'PostGIS': {'host': 'localhost', 'port': 5432, 'user': 'u', 'password': 'p', 'database': 'db'},
        },
        'smtp_options': {'host': 'localhost', 'username': 'u', 'password': 'p'},
        'output': {'type': 'Excel', 'excel': {'output_dir': str(tmp_path / 'RSA_OneDrive')}},
        'report_execution': {'mode': 'sequential'},
    }
    settings_path = tmp_path / 'settings.json'
    settings_path.write_text(json.dumps(settings), encoding='utf-8')

    monkeypatch.setattr('outputs.excel_wrapper.SingleExcelWriter.init', lambda *args, **kwargs: None)
    monkeypatch.setattr('outputs.sheets_wrapper.SingleSheetsWrapper.init', lambda *args, **kwargs: None)

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn
    mock_connector = MagicMock()
    mock_connector.pool = mock_pool
    monkeypatch.setattr('lib.reports.ReportLoopRunner.SinglePostGISConnector.get_connector', lambda: mock_connector)

    runner = ReportLoopRunner(str(settings_path))
    runner._preflight_checks()

    mock_pool.getconn.assert_called_once()
    mock_cur.execute.assert_called_once_with("SELECT 1")
    mock_pool.putconn.assert_called_once_with(mock_conn)


def test_preflight_checks_failure(monkeypatch, tmp_path):
    settings = {
        'databases': {
            'PostGIS': {'host': 'localhost', 'port': 5432, 'user': 'u', 'password': 'p', 'database': 'db'},
        },
        'smtp_options': {'host': 'localhost', 'username': 'u', 'password': 'p'},
        'output': {'type': 'Excel', 'excel': {'output_dir': str(tmp_path / 'RSA_OneDrive')}},
        'report_execution': {'mode': 'sequential'},
    }
    settings_path = tmp_path / 'settings.json'
    settings_path.write_text(json.dumps(settings), encoding='utf-8')

    monkeypatch.setattr('outputs.excel_wrapper.SingleExcelWriter.init', lambda *args, **kwargs: None)
    monkeypatch.setattr('outputs.sheets_wrapper.SingleSheetsWrapper.init', lambda *args, **kwargs: None)

    mock_pool = MagicMock()
    mock_pool.getconn.side_effect = RuntimeError("connection refused")
    mock_connector = MagicMock()
    mock_connector.pool = mock_pool
    monkeypatch.setattr('lib.reports.ReportLoopRunner.SinglePostGISConnector.get_connector', lambda: mock_connector)

    enqueue_calls = []
    monkeypatch.setattr('lib.reports.ReportLoopRunner.enqueue_sqlite_job', lambda action, payload: enqueue_calls.append((action, payload)))

    runner = ReportLoopRunner(str(settings_path))
    runner.pipeline_status = None

    with pytest.raises(RuntimeError, match="PostGIS preflight check failed: connection refused"):
        runner._preflight_checks()

    assert len(enqueue_calls) == 0
