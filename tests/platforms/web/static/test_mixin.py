import pytest

from briefcase.console import Console
from briefcase.platforms.web.static import StaticWebCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return StaticWebCreateCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_project_path(create_command, first_app_config, tmp_path):
    project_path = create_command.project_path(first_app_config)

    assert project_path == (tmp_path / "base_path/build/first-app/web/static/www")


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "web"
        / "static"
        / "www"
        / "index.html"
    )


def test_wheel_path(create_command, first_app_config, tmp_path):
    wheel_path = create_command.wheel_path(first_app_config)

    assert wheel_path == (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "web"
        / "static"
        / "www"
        / "static"
        / "wheels"
    )


def test_distribution_path(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config)

    assert distribution_path == (tmp_path / "base_path/dist/First App-0.0.1.web.zip")
