import os
import sys
import threading
import time

import pytest
import tenacity


def test_rename_path(mock_tools, tmp_path):
    def openclose(filepath):
        handler = filepath.open(encoding="UTF-8")
        time.sleep(1)
        handler.close()

    (tmp_path / "orig-dir-1").mkdir()
    tl = tmp_path / "orig-dir-1/orig-file"
    tl.touch()
    file_access_thread = threading.Thread(target=openclose, args=(tl,))
    rename_thread = threading.Thread(
        target=mock_tools.files.path_rename,
        args=(tmp_path / "orig-dir-1", tmp_path / "new-dir-1"),
    )

    file_access_thread.start()
    rename_thread.start()

    rename_thread.join()

    assert "new-dir-1" in os.listdir(tmp_path)


@pytest.mark.xfail(
    sys.platform == "win32",
    raises=tenacity.RetryError,
    reason="Windows can't rename folder in filepath when the file is open",
)
def test_rename_path_fail(mock_tools, tmp_path, monkeypatch):
    (tmp_path / "orig-dir-2").mkdir()
    (tmp_path / "orig-dir-2/orig-file").touch()

    with (tmp_path / "orig-dir-2/orig-file").open(encoding="UTF-8"):

        monkeypatch.setattr(tenacity.nap.time, "sleep", lambda x: True)
        mock_tools.files.path_rename(tmp_path / "orig-dir-2", tmp_path / "new-dir-2")
