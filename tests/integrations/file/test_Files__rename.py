import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import tenacity


def test_rename_path(mock_tools, tmp_path):
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
    mock_tools.file.path_rename(tmp_path / "orig-dir-1", tmp_path / "new-dir-1")
    file_access_thread.join()

    assert "new-dir-1" in os.listdir(tmp_path)


def test_rename_path_file_not_found(mock_tools, tmp_path):
    """A FileNotFoundError is raised immediately without retrying."""
    with pytest.raises(FileNotFoundError):
        mock_tools.file.path_rename(tmp_path / "does-not-exist", tmp_path / "new-name")


def test_rename_path_fail(mock_tools, tmp_path, monkeypatch):
    """Retries are exhausted when rename repeatedly raises PermissionError."""
    monkeypatch.setattr(tenacity.nap.time, "sleep", lambda x: True)
    monkeypatch.setattr(Path, "rename", MagicMock(side_effect=PermissionError))

    with pytest.raises(tenacity.RetryError):
        mock_tools.file.path_rename(tmp_path / "orig-dir-2", tmp_path / "new-dir-2")
