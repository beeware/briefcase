from zipfile import ZipFile

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import StaticWebPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = StaticWebPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.data_path = tmp_path / "briefcase"
    return command


def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["zip"]


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == "zip"


def test_package_app(package_command, first_app_built, tmp_path):
    "An app can be packaged for distribution"

    package_command.package_app(first_app_built, "zip")

    # The packaged archive exists, and contains all the www files,
    # but without the www prefix.
    archive_file = tmp_path / "base_path" / "web" / "First App-0.0.1.zip"
    assert archive_file.exists()
    with ZipFile(archive_file) as archive:
        assert sorted(archive.namelist()) == [
            "index.html",
            "pyscript.toml",
            "static/",
            "static/css/",
            "static/css/briefcase.css",
            "static/wheels/",
            "static/wheels/dummy-1.2.3-py3-none-any.whl",
        ]
