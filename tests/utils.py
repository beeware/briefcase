import os
import zipfile
from unittest.mock import MagicMock

from briefcase.console import Console, InputDisabled


class DummyConsole(Console):
    def __init__(self, *values, enabled=True):
        super().__init__(enabled=enabled)
        self.prompts = []
        self.values = list(values)

    def __call__(self, prompt):
        if not self.enabled:
            raise InputDisabled()
        self.prompts.append(prompt)
        return self.values.pop(0)


# Consider to remove  class definition when we drop python 3.7 support.
class FsPathMock(MagicMock):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def __fspath__(self):
        return self.path

    def _get_child_mock(self, **kw):
        """Create child mocks with right MagicMock class."""
        return MagicMock(**kw)


def create_file(filepath, content, mode="w", chmod=None):
    """A test utility to create a file with known content.

    Ensures that the directory for the file exists, and writes a file with
    specific content.

    :param filepath: The path for the file to create
    :param content: A string containing the content to write.
    :param mode: The mode to open the file. This is `w` by default;
        use `wb` and provide content as a bitstring if you need to
        write a binary file.
    :returns: The path to the file that was created.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open(mode) as f:
        f.write(content)

    if chmod:
        os.chmod(filepath, chmod)

    return filepath


def create_zip_file(zippath, content):
    """A test utility to create a file with known content.

    Ensures that the directory for the file exists, and writes a file with
    specific content.

    :param zippath: The path for the ZIP file to create
    :param content: A list of pairs; each pair is (path, data) describing
        an item to be added to the zip file.
    :returns: The path to the file that was created.
    """
    zippath.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zippath, "w") as f:
        for path, data in content:
            f.writestr(path, data=data)

    return zippath


def mock_file_download(filename, content, mode="w", role=None):
    """Create a side effect function that mocks the download of a zip file.

    :param filename: The file name (*not* the path - just the file name) to
        create as a side effect
    :param content: A string containing the content to write.
    :param mode: The mode to open the file. This is `w` by default;
        use `wb` and provide content as a bitstring if you need to
        write a binary file.
    :param role: The role played by the content being downloaded
    :returns: a function that can act as a mock side effect for `download_file()`
    """

    def _download_file(url, download_path, role):
        return create_file(download_path / filename, content, mode=mode)

    return _download_file


def mock_zip_download(filename, content, role=None):
    """Create a side effect function that mocks the download of a zip file.

    :param content: A string containing the content to write.
    :returns: a function that can act as a mock side effect for `download_file()`
    """

    def _download_file(url, download_path, role):
        return create_zip_file(download_path / filename, content)

    return _download_file
