import json

from lib.reports.ReportLoopRunner import ReportLoopRunner


class DummyReport:
	def __init__(self):
		self.report = None
		self.runs = 0

	def init_report(self) -> None:
		self.report = object()

	def run_report(self, sender) -> None:
		self.runs += 1
		if self.runs == 1:
			raise RuntimeError('boom')


def test_retry_pass_reinitializes_database_connections(monkeypatch, tmp_path):
	settings = {
		'databases': {
			'Neo4j': {'uri': 'bolt://example', 'user': 'u', 'password': 'p', 'database': 'neo4j'},
			'PostGIS': {'host': 'localhost', 'port': 5432, 'user': 'u', 'password': 'p', 'database': 'db'},
			'ArangoDB': {'host': 'localhost', 'port': 8529, 'user': 'u', 'password': 'p', 'database': 'db'},
		},
		'smtp_options': {'host': 'localhost', 'username': 'u', 'password': 'p'},
		'output': {'type': 'Excel', 'excel': {'output_dir': str(tmp_path / 'RSA_OneDrive')}},
		'report_execution': {'mode': 'sequential'},
	}
	settings_path = tmp_path / 'settings.json'
	settings_path.write_text(json.dumps(settings), encoding='utf-8')

	refresh_calls: list[dict] = []
	monkeypatch.setattr('lib.reports.ReportLoopRunner.SingleSheetsWrapper.init', lambda *args, **kwargs: None)
	monkeypatch.setattr('outputs.excel_wrapper.SingleExcelWriter.init', lambda *args, **kwargs: None)
	monkeypatch.setattr('lib.reports.ReportLoopRunner.reinitialize_database_connections', lambda cfg: refresh_calls.append(cfg))
	monkeypatch.setattr('lib.reports.ReportLoopRunner.process_once', lambda *args, **kwargs: 0)
	monkeypatch.setattr('lib.reports.ReportLoopRunner.MailSender.send_all_mails', lambda self: None)
	monkeypatch.setattr(ReportLoopRunner, 'adjust_mailed_info_in_sheets', lambda self, sender: None)

	dummy_report = DummyReport()
	monkeypatch.setattr('lib.reports.ReportLoopRunner.create_report_instance', lambda name: dummy_report)

	runner = ReportLoopRunner(str(settings_path))
	runner._run_sequential(['DummyReport'])

	assert dummy_report.runs == 2
	assert len(refresh_calls) == 2

