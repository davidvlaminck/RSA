from scripts.ops.gdrive_upload import _should_skip


def test_should_skip_legacy_archive_folder_names():
    assert _should_skip('Archief')
    assert _should_skip('archivedreports')
    assert not _should_skip('Overzicht')

