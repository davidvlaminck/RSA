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


