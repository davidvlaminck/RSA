from outputs.summary_stager import clear_staged_processed


def test_clear_staged_processed_empties_contents(tmp_path):
    staged_dir = tmp_path / 'RSA_OneDrive' / 'staged_summaries'
    processed = staged_dir / 'processed'
    (processed / 'nested').mkdir(parents=True, exist_ok=True)
    (processed / 'nested' / 'payload.json').write_text('{}', encoding='utf-8')
    (processed / 'stale.json').write_text('{}', encoding='utf-8')

    cleared = clear_staged_processed(staged_dir)

    assert cleared == processed
    assert processed.exists()
    assert list(processed.iterdir()) == []


def test_clear_staged_processed_removes_uncategorized_payloads(tmp_path):
    staged_dir = tmp_path / 'RSA_OneDrive' / 'staged_summaries'
    (staged_dir / 'processed').mkdir(parents=True, exist_ok=True)
    (staged_dir / 'processing').mkdir(parents=True, exist_ok=True)
    (staged_dir / 'failed').mkdir(parents=True, exist_ok=True)
    (staged_dir / '20261109T000000_write_cell_report0002_def.json').write_text('{}', encoding='utf-8')
    (staged_dir / '20261125T044906_append_row_report0000_abc.json').write_text('{}', encoding='utf-8')
    (staged_dir / 'processing' / 'leftover.json').write_text('{}', encoding='utf-8')
    (staged_dir / 'failed' / 'broken.json').write_text('{}', encoding='utf-8')

    cleared = clear_staged_processed(staged_dir)

    assert cleared == staged_dir / 'processed'
    assert list(staged_dir.glob('*.json')) == []
    assert list((staged_dir / 'processing').iterdir()) == []
    assert list((staged_dir / 'failed').iterdir()) == []
    assert list((staged_dir / 'processed').iterdir()) == []


