import io
import os
import tarfile
import zipfile

from briefcase.console import Console, InputDisabled


class DummyConsole(Console):
    def __init__(self, *values, enabled=True):
        super().__init__(enabled=enabled)
        self.prompts = []
        self.values = list(values)

    def __call__(self, prompt, *args, **kwargs):
        if not self.enabled:
            raise InputDisabled()
        self.prompts.append(prompt)
        return self.values.pop(0)


def create_file(filepath, content, mode="w", chmod=None):
    """A test utility to create a file with known content.

    Ensures that the directory for the file exists, and writes a file with
    specific content.

    :param filepath: The path for the file to create
    :param content: A string containing the content to write.
    :param mode: The mode to open the file. This is `w` by default;
        use `wb` and provide content as a bitstring if you need to
        write a binary file.
    :param chmod: file permissions to apply
    :returns: The path to the file that was created.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open(mode) as f:
        f.write(content)

    if chmod:
        os.chmod(filepath, chmod)

    return filepath


def create_zip_file(zippath, content):
    """A test utility to create a .zip file with known content.

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


def create_tgz_file(tgzpath, content):
    """A test utility to create a .tar.gz file with known content.

    Ensures that the directory for the file exists, and writes a file with
    specific content.

    :param tgzpath: The path for the ZIP file to create
    :param content: A list of pairs; each pair is (path, data) describing
        an item to be added to the zip file.
    :returns: The path to the file that was created.
    """
    tgzpath.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tgzpath, "w:gz") as f:
        for path, data in content:
            tarinfo = tarfile.TarInfo(path)
            payload = data.encode("utf-8")
            tarinfo.size = len(payload)
            f.addfile(tarinfo, io.BytesIO(payload))

    return tgzpath


def mock_file_download(filename, content, mode="w", role=None):
    """Create a side effect function that mocks the download of a zip file.

    :param filename: The file name (*not* the path - just the file name) to
        create as a side effect
    :param content: A string containing the content to write.
    :param mode: The mode to open the file. This is `w` by default;
        use `wb` and provide content as a bitstring if you need to
        write a binary file.
    :param role: The role played by the content being downloaded
    :returns: a function that can act as a mock side effect for `download.file()`
    """

    def _download_file(url, download_path, role):
        return create_file(download_path / filename, content, mode=mode)

    return _download_file


def mock_zip_download(filename, content, role=None):
    """Create a side effect function that mocks the download of a zip file.

    :param filename: The file name (*not* the path - just the file name) to
        create as a side effect
    :param content: A string containing the content to write.
    :param role: The role played by the content being downloaded
    :returns: a function that can act as a mock side effect for `download.file()`
    """

    def _download_file(url, download_path, role):
        return create_zip_file(download_path / filename, content)

    return _download_file


def mock_tgz_download(filename, content, role=None):
    """Create a side effect function that mocks the download of a .tar.gz file.

    :param content: A string containing the content to write.
    :returns: a function that can act as a mock side effect for `download.file()`
    """

    def _download_file(url, download_path, role):
        return create_tgz_file(download_path / filename, content)

    return _download_file


def create_wheel(path, package="dummy", version="1.2.3", extra_content=None):
    """Create a sample wheel file.

    :param path: The folder where the wheel should be writter.
    :param package: The name of the package in the wheel. Defaults to ``dummy``
    :param version: The version number of the package. Defaults to ``1.2.3``
    :param extra_content: Optional. A list of tuples of ``(path, content)`` that
        will be added to the wheel.
    """
    wheel_filename = path / f"{package}-{version}-py3-none-any.whl"

    create_zip_file(
        wheel_filename,
        content=[
            (f"{package}/__init__.py", ""),
            (f"{package}/app.py", "# This is the app"),
        ]
        + (extra_content if extra_content else [])
        + [
            # Create an empty dist-info
            (f"{package}-{version}.dist-info/INSTALLER", ""),
            (f"{package}-{version}.dist-info/METADATA", ""),
            (f"{package}-{version}.dist-info/WHEEL", ""),
            (f"{package}-{version}.dist-info/top_level.txt", ""),
            (f"{package}-{version}.dist-info/RECORD", ""),
        ],
    )

    return wheel_filename
