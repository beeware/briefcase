from __future__ import annotations

import io
import os
import plistlib
import tarfile
import zipfile
from email.message import EmailMessage
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from rich.markup import escape
from urllib3.util.retry import Retry

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


def default_rich_prompt(prompt: str) -> str:
    """Formats a prompt as what is actually passed to Rich."""
    return f"[bold]{escape(prompt)}[/bold]"


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
    with filepath.open(mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f:
        f.write(content)

    if chmod:
        os.chmod(filepath, chmod)

    return filepath


def create_plist_file(plistpath, content):
    """A test utility to create a plist file with known content.

    Ensures that the directory for the file exists, and writes an XML plist with
    specific content.

    :param plistpath: The path for the plist file to create.
    :param content: A dictionary of content that plistlib can use to create the plist
        file.
    :returns: The path to the file that was created.
    """
    plistpath.parent.mkdir(parents=True, exist_ok=True)
    with plistpath.open("wb") as f:
        plistlib.dump(content, f)

    return plistpath


def create_zip_file(zippath, content):
    """A test utility to create a .zip file with known content.

    Ensures that the directory for the file exists, and writes a file with specific
    content.

    :param zippath: The path for the ZIP file to create
    :param content: A list of pairs; each pair is (path, data) describing an item to be
        added to the zip file.
    :returns: The path to the file that was created.
    """
    zippath.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zippath, "w") as f:
        for path, data in content:
            f.writestr(path, data=data)

    return zippath


def create_tgz_file(tgzpath, content):
    """A test utility to create a .tar.gz file with known content.

    Ensures that the directory for the file exists, and writes a file with specific
    content.

    :param tgzpath: The path for the ZIP file to create
    :param content: A list of pairs; each pair is (path, data) describing an item to be
        added to the zip file.
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


def distinfo_metadata(
    package: str = "dummy",
    version: str = "1.2.3",
    tag: str = "py3-none-any",
):
    """Generate the content for a distinfo folder.

    :param package: The name of the package.
    :param version: The version number of the package.
    :param tag: The packaging tag for the package.
    """
    content = []

    # INSTALLER
    installer = "pip\n"
    content.append((f"{package}-{version}.dist-info/INSTALLER", installer))

    # METADATA
    metadata = EmailMessage()
    metadata["Metadata-Version"] = "2.1"
    metadata["Name"] = package
    metadata["Version"] = version
    metadata["Summary"] = f"A packaged named {package}."
    metadata["Author-email"] = "Jane Developer <jane@example.com>"
    content.append((f"{package}-{version}.dist-info/METADATA", str(metadata)))

    # WHEEL
    wheel = EmailMessage()
    wheel["Wheel-Version"] = "1.0"
    wheel["Generator"] = "test-case"
    wheel["Root-Is-Purelib"] = "true" if tag == "py3-none-any" else "false"
    wheel["Tag"] = tag
    content.append((f"{package}-{version}.dist-info/WHEEL", str(wheel)))

    # RECORD
    # Create the file, but don't actually populate it.
    record = ""
    content.append((f"{package}-{version}.dist-info/RECORD", record))

    return content


def installed_package_content(
    package="dummy",
    version="1.2.3",
    tag="py3-none-any",
    extra_content=None,
):
    """Generate the content for an installed package.

    :param path: The site-packages folder into which to install the package.
    :param package: The name of the package in the wheel. Defaults to ``dummy``
    :param version: The version number of the package. Defaults to ``1.2.3``
    :param tag: The installation tag for the package. Defaults to a pure python wheel.
    :param extra_content: Optional. A list of tuples of ``(path, content)`` that will be
        added to the wheel.
    """
    return (
        [
            (f"{package}/__init__.py", ""),
            (f"{package}/app.py", "# This is the app"),
        ]
        + (extra_content if extra_content else [])
        + distinfo_metadata(package=package, version=version, tag=tag)
    )


def create_installed_package(
    path,
    package="dummy",
    version="1.2.3",
    tag="py3-none-any",
    extra_content=None,
):
    """Write an installed package into a 'site-packages' folder.

    :param path: The site-packages folder into which to install the package.
    :param package: The name of the package in the wheel. Defaults to ``dummy``
    :param version: The version number of the package. Defaults to ``1.2.3``
    :param tag: The installation tag for the package. Defaults to a pure python wheel.
    :param extra_content: Optional. A list of tuples of ``(path, content)`` or
        ``(path, content, chmod)`` that will be added to the wheel. If ``chmod`` is
        not specified, default filesystem permissions will be used.
    """
    for entry in installed_package_content(
        package=package,
        version=version,
        tag=tag,
        extra_content=extra_content,
    ):
        try:
            filename, content, chmod = entry
        except ValueError:
            filename, content = entry
            chmod = None
        create_file(path / filename, content=content, chmod=chmod)


def create_wheel(
    path,
    package="dummy",
    version="1.2.3",
    tag="py3-none-any",
    extra_content=None,
):
    """Create a sample wheel file.

    :param path: The folder where the wheel should be written.
    :param package: The name of the package in the wheel. Defaults to ``dummy``
    :param version: The version number of the package. Defaults to ``1.2.3``
    :param tag: The installation tag for the package. Defaults to a pure python wheel.
    :param extra_content: Optional. A list of tuples of ``(path, content)`` or
        ``(path, content, chmod)`` that will be added to the wheel. If ``chmod`` is
        not specified, default filesystem permissions will be used.
    """
    wheel_filename = path / f"{package}-{version}-{tag}.whl"

    create_zip_file(
        wheel_filename,
        content=installed_package_content(
            package=package,
            version=version,
            tag=tag,
            extra_content=extra_content,
        ),
    )

    return wheel_filename


def file_content(path: Path) -> str | None:
    """Return the content of a file, or None if the path is a directory."""
    if path.is_dir():
        return None
    with path.open(encoding="utf-8") as f:
        return f.read()


def assert_url_resolvable(url: str):
    """Tests whether a URL is resolvable with retries; raises for failure."""
    with requests.session() as sess:
        adapter = HTTPAdapter(max_retries=Retry(status_forcelist={500, 502, 504}))
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)

        sess.head(url).raise_for_status()
