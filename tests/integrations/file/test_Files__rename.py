import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import tenacity


def test_rename_path(mock_tools, tmp_path):
    """Rename succeeds even when a file inside the directory is temporarily open.

    On Windows, renaming a directory while a file inside it is open raises a
    PermissionError. This test simulates that scenario by opening a file in a background
    thread, sleeping briefly, then closing it — verifying that the rename retries until
    the file is released and ultimately succeeds.
    """

    def openclose(filepath):
        handler = filepath.open(encoding="UTF-8")
        try:
            time.sleep(0.1)
        finally:
            handler.close()

    (tmp_path / "orig-dir-1").mkdir()
    tl = tmp_path / "orig-dir-1/orig-file"
    tl.touch()
    file_access_thread = threading.Thread(target=openclose, args=(tl,))

    file_access_thread.start()
    # Sleep briefly so the background thread has time to open the file before
    # the rename is attempted, ensuring the retry logic is exercised.
    time.sleep(0.05)
    mock_tools.file.rename(tmp_path / "orig-dir-1", tmp_path / "new-dir-1")
    file_access_thread.join()

    assert "new-dir-1" in os.listdir(tmp_path)


def test_rename_path_file_not_found(mock_tools, tmp_path, monkeypatch):
    """A FileNotFoundError is raised immediately without retrying."""
    mock_rename = MagicMock(side_effect=FileNotFoundError)
    monkeypatch.setattr(Path, "rename", mock_rename)

    with pytest.raises(FileNotFoundError):
        mock_tools.file.rename(tmp_path / "does-not-exist", tmp_path / "new-name")

    # rename should have been called exactly once — no retries
    mock_rename.assert_called_once()


def test_rename_path_fail(mock_tools, tmp_path, monkeypatch):
    """Retries are exhausted when rename repeatedly raises PermissionError."""
    mock_sleep = MagicMock()
    monkeypatch.setattr(tenacity.nap.time, "sleep", mock_sleep)
    mock_rename = MagicMock(side_effect=PermissionError)
    monkeypatch.setattr(Path, "rename", mock_rename)

    with pytest.raises(tenacity.RetryError):
        mock_tools.file.rename(tmp_path / "orig-dir-2", tmp_path / "new-dir-2")

    # 25 attempts total → 24 sleeps of 0.2 s each
    assert mock_rename.call_count == 25
    assert mock_sleep.call_count == 24
    mock_sleep.assert_called_with(0.2)
