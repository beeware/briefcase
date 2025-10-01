import pytest
from briefcase.platforms.web.static.build import StaticWebBuildCommand

from briefcase.console import Console


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.fixture
def app_config(first_app_config, tmp_path):
    first_app_config._path = tmp_path / "base_path/build/first-app/web/static"
    (first_app_config._path / "www").mkdir(parents=True)
    return first_app_config


def write_target_file(base_path, rel_filename, content):
    target = base_path / "www" / rel_filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
