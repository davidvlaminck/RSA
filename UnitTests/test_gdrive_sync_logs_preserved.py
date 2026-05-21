from pathlib import Path

from scripts.ops import gdrive_upload


def test_sync_down_cleanup_preserves_logs_folder(tmp_path, monkeypatch):
	local_folder = tmp_path / 'RSA_OneDrive'
	logs_dir = local_folder / 'logs'
	logs_dir.mkdir(parents=True)
	run_log = logs_dir / 'run_20260520.log'
	run_log.write_text('existing log\n', encoding='utf-8')

	# Content that should be wiped by sync-down cleanup.
	stale_file = local_folder / 'stale.xlsx'
	stale_file.write_text('old', encoding='utf-8')
	stale_dir = local_folder / '0000-0099'
	stale_dir.mkdir()
	(stale_dir / 'old.xlsx').write_text('old', encoding='utf-8')

	token_path = tmp_path / 'token.pkl'
	token_path.write_bytes(b'token')

	monkeypatch.setattr(gdrive_upload, '_build_service', lambda token_path: object())
	monkeypatch.setattr(gdrive_upload, '_get_or_create_folder_path', lambda service, name: 'folder-id')

	def fake_download_tree(service, folder_id, local_path: Path, is_root: bool = False):
		(local_path / 'Overzicht').mkdir(exist_ok=True)
		(local_path / 'Overzicht' / '[RSA] Overzicht rapporten.xlsx').write_text('new', encoding='utf-8')

	monkeypatch.setattr(gdrive_upload, '_download_tree', fake_download_tree)

	ok = gdrive_upload.sync_drive_to_local(
		local_folder=str(local_folder),
		drive_folder_name='RSA',
		token_path=str(token_path),
	)

	assert ok is True
	assert run_log.exists()
	assert run_log.read_text(encoding='utf-8') == 'existing log\n'
	assert not stale_file.exists()
	assert not stale_dir.exists()
	assert (local_folder / 'Overzicht' / '[RSA] Overzicht rapporten.xlsx').exists()

