import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import StaticWebCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return StaticWebCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_output_format_template_context_with_style_framework(
    create_command, first_app_config
):
    """If the app defines a style framework, it is included in the template
    context."""
    first_app_config.style_framework = "Souperstyler v1.2"

    assert create_command.output_format_template_context(first_app_config) == {
        "style_framework": "Souperstyler v1.2",
    }


def test_output_format_template_context_without_style_framework(
    create_command,
    first_app_config,
):
    """If the app doesn't define a style framework, the template context still
    has an entry."""
    assert create_command.output_format_template_context(first_app_config) == {
        "style_framework": "None",
    }
