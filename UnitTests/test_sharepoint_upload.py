from scripts.ops import sharepoint_sync


class _FakeClient:
    def __init__(self):
        self.library_id = 'aimdata-lib-id'
        self.validate_ok = True
        self.validate_reason = ''
        self.sync_local_called = False
        self.sync_local_result = True
        self.sync_remote_called = False
        self.sync_remote_result = True
        self.write_log_calls = []
        self.prune_calls = []

    def get_document_library_by_name(self, name):
        return {'id': self.library_id} if name == 'AIMData' else None

    def validate_local_mirror(self, local_folder):
        return self.validate_ok, self.validate_reason

    def sync_local_to_library(self, local_folder, folder, lib_id):
        self.sync_local_called = True
        self.sync_local_args = (local_folder, folder, lib_id)
        return self.sync_local_result

    def sync_library_to_local(self, folder, local_folder, lib_id):
        self.sync_remote_called = True
        self.sync_remote_args = (folder, local_folder, lib_id)
        return self.sync_remote_result

    def write_daily_run_log(self, local_folder, status, details=''):
        self.write_log_calls.append((local_folder, status, details))

    def prune_daily_run_logs(self, local_folder, keep=14):
        self.prune_calls.append((local_folder, keep))


def test_sync_local_to_sharepoint_success(monkeypatch, tmp_path):
    fake = _FakeClient()
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    local = tmp_path / 'RSA_OneDrive'
    local.mkdir()
    ok = sharepoint_sync.sync_local_to_sharepoint(local)
    assert ok is True
    assert fake.sync_local_called
    assert fake.sync_local_args[1] == 'RSA'


def test_sync_local_to_sharepoint_blocked_on_validation(monkeypatch, tmp_path):
    fake = _FakeClient()
    fake.validate_ok = False
    fake.validate_reason = 'missing overzicht'
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    local = tmp_path / 'RSA_OneDrive'
    local.mkdir()
    ok = sharepoint_sync.sync_local_to_sharepoint(local)
    assert ok is False
    assert not fake.sync_local_called


def test_sync_sharepoint_to_local_success(monkeypatch, tmp_path):
    fake = _FakeClient()
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    local = tmp_path / 'RSA_OneDrive'
    local.mkdir()
    ok = sharepoint_sync.sync_sharepoint_to_local(local)
    assert ok is True
    assert fake.sync_remote_called


def test_sync_sharepoint_to_local_blocked_on_validation(monkeypatch, tmp_path):
    fake = _FakeClient()
    fake.validate_ok = False
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    local = tmp_path / 'RSA_OneDrive'
    local.mkdir()
    ok = sharepoint_sync.sync_sharepoint_to_local(local)
    assert ok is False
    assert not fake.sync_remote_called


def test_download_before_run_delegates(monkeypatch, tmp_path):
    fake = _FakeClient()
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    local = tmp_path / 'RSA_OneDrive'
    local.mkdir()
    ok = sharepoint_sync.download_before_run(local)
    assert ok is True
    assert fake.sync_remote_called


def test_write_daily_run_log_and_prune(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(sharepoint_sync, '_client', lambda: fake)
    sharepoint_sync.write_daily_run_log('local', 'POST_RUN_UPLOAD_DONE', 'details')
    sharepoint_sync.prune_daily_run_logs('local', keep=7)
    assert fake.write_log_calls == [('local', 'POST_RUN_UPLOAD_DONE (details)', '')]
    assert fake.prune_calls == [('local', 7)]
