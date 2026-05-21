from scripts.ops import gdrive_upload
from scripts.ops.gdrive_upload import _should_skip


def test_should_skip_legacy_archive_folder_names():
    assert _should_skip('Archief')
    assert _should_skip('archivedreports')
    assert not _should_skip('Overzicht')


class _FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FakeFiles:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []

    def list(self, **kwargs):
        return _FakeRequest({'files': []})

    def create(self, body=None, media_body=None, fields=None):
        body = body or {}
        self.created.append(body)
        if body.get('mimeType') == gdrive_upload.FOLDER_MIME:
            return _FakeRequest({'id': f"folder-{len(self.created)}", 'mimeType': gdrive_upload.FOLDER_MIME})
        return _FakeRequest({'id': f"file-{len(self.created)}"})

    def update(self, fileId=None, media_body=None):
        self.updated.append(fileId)
        return _FakeRequest({})

    def delete(self, fileId=None):
        self.deleted.append(fileId)
        return _FakeRequest({})


class _FakeService:
    def __init__(self):
        self._files = _FakeFiles()

    def files(self):
        return self._files


def test_sync_local_dir_skips_root_files_and_staged_summaries(monkeypatch, tmp_path):
    root = tmp_path / 'RSA_OneDrive'
    bucket = root / '0000-0099'
    staged = root / 'staged_summaries'
    bucket.mkdir(parents=True)
    staged.mkdir(parents=True)
    (root / 'root.xlsx').write_text('root', encoding='utf-8')
    (staged / 'processed').mkdir(parents=True)
    (bucket / 'report.xlsx').write_text('bucket', encoding='utf-8')

    service = _FakeService()

    def fake_list_children(_service, folder_id):
        if folder_id == 'root-folder':
            return [
                {'name': 'root.xlsx', 'id': 'root-file', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
                {'name': 'staged_summaries', 'id': 'staged-folder', 'mimeType': gdrive_upload.FOLDER_MIME},
                {'name': '0000-0099', 'id': 'bucket-folder', 'mimeType': gdrive_upload.FOLDER_MIME},
            ]
        if folder_id == 'bucket-remote':
            return []
        return []

    monkeypatch.setattr(gdrive_upload, '_list_children', fake_list_children)

    gdrive_upload._sync_local_dir_to_drive(service, root, 'root-folder', is_root=True)

    created_names = [entry.get('name') for entry in service.files().created]
    assert 'root.xlsx' not in created_names
    assert 'staged_summaries' not in created_names
    assert 'report.xlsx' in created_names


def test_sync_local_dir_skips_root_files_for_custom_root_name(monkeypatch, tmp_path):
    root = tmp_path / 'CustomLocalMirror'
    bucket = root / '0000-0099'
    bucket.mkdir(parents=True)
    (root / 'should_not_upload.xlsx').write_text('root', encoding='utf-8')
    (bucket / 'report.xlsx').write_text('bucket', encoding='utf-8')

    service = _FakeService()

    def fake_list_children(_service, folder_id):
        if folder_id == 'root-folder':
            return []
        return []

    monkeypatch.setattr(gdrive_upload, '_list_children', fake_list_children)

    gdrive_upload._sync_local_dir_to_drive(service, root, 'root-folder', is_root=True)

    created_names = [entry.get('name') for entry in service.files().created]
    assert 'should_not_upload.xlsx' not in created_names
    assert 'report.xlsx' in created_names


def test_get_or_create_folder_path_uses_root_and_parent_scoped_queries(monkeypatch):
    queries = []

    class _PathFakeFiles:
        def list(self, **kwargs):
            queries.append(kwargs.get('q', ''))
            q = kwargs.get('q', '')
            if "name='RSA'" in q:
                return _FakeRequest({'files': [{'id': 'rsa-root', 'name': 'RSA'}]})
            if "name='RSA_OneDrive'" in q:
                return _FakeRequest({'files': []})
            return _FakeRequest({'files': []})

        def create(self, body=None, media_body=None, fields=None):
            return _FakeRequest({'id': 'onedrive-folder'})

    class _PathFakeService:
        def files(self):
            return _PathFakeFiles()

    folder_id = gdrive_upload._get_or_create_folder_path(_PathFakeService(), 'RSA/RSA_OneDrive')

    assert folder_id == 'onedrive-folder'
    assert any("name='RSA'" in q and "'root' in parents" in q for q in queries)
    assert any("name='RSA_OneDrive'" in q and "'rsa-root' in parents" in q for q in queries)


