from scripts.ops.dry_sync_test import inspect_local_layout, load_config
def test_inspect_local_layout_counts_root_files_and_overview(tmp_path):
    root = tmp_path / 'RSA_OneDrive'
    overview = root / 'Overzicht'
    bucket = root / '0000-0099'
    overview.mkdir(parents=True)
    bucket.mkdir(parents=True)
    (root / 'root.xlsx').write_text('x', encoding='utf-8')
    (overview / '[RSA] Overzicht rapporten.xlsx').write_text('x', encoding='utf-8')
    stats = inspect_local_layout(root)
    assert stats['root_files'] == 1
    assert stats['bucket_dirs'] == 2
    assert stats['overview_files'] == 1
    assert stats['summary_files'] == 1
def test_load_config_resolves_relative_paths(tmp_path):
    settings = tmp_path / 'settings.json'
    settings.write_text(
        '{"drive_sync": {"local_folder": "RSA_OneDrive", "drive_folder": "RSA", "token_path": "token.pkl"}, "google_api": {"credentials_path": "cred.json"}}',
        encoding='utf-8',
    )
    cfg = load_config(str(settings))
    assert cfg.local_folder == tmp_path / 'RSA_OneDrive'
    assert cfg.drive_folder == 'RSA'
    assert cfg.token_path == tmp_path / 'token.pkl'
    assert cfg.credentials_path == tmp_path / 'cred.json'
