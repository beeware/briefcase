import os
import platform
import tomllib
from datetime import date
from pathlib import Path

import pytest

import briefcase
from briefcase.exceptions import (
    CorruptContentError,
)

from ...utils import create_json_file, create_toml_file


@pytest.fixture
def full_context():
    return {
        "format": "dummy",
        "app_name": "my-app",
        "formal_name": "My App",
        "bundle": "com.example",
        "bundle_identifier": "com.example.my-app",
        "version": "1.2.3",
        "description": "This is a simple app",
        "long_description": None,
        "sources": ["src/my_app"],
        "test_sources": None,
        "test_requires": None,
        "debugger": None,
        "debugger_host": None,
        "debugger_port": None,
        "url": "https://example.com",
        "authors": [{"name": "First Last", "email": "first@example.com"}],
        "requires": None,
        "icon": None,
        "supported": True,
        "console_app": False,
        "permissions": {},
        "custom_permissions": {},
        "requests": {},
        "document_types": {},
        "install_options": {},
        "uninstall_options": {},
        "license": {"file": "LICENSE"},
        "license_files": [],
        "requirement_installer_args": [],
        "external_package_path": None,
        "external_package_executable_path": None,
        "install_launcher": True,
        "test_mode": False,
        "env_manager": "venv",
        # Properties of the generating environment
        "python_version": platform.python_version(),
        "host_arch": "gothic",
        "is_32bit_python": False,
        "briefcase_version": briefcase.__version__,
        # Properties of the template
        "template_source": (
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git"
        ),
        "template_branch": f"v{briefcase.__version__}",
        # Fields generated from other properties
        "module_name": "my_app",
        "class_name": "MyApp",
        "package_name": "com.example",
        # Date-based fields added at time of generation
        "year": date.today().strftime("%Y"),
        "month": date.today().strftime("%B"),
        # Fields added by the output format.
        "output_format": "dummy",
    }


def mock_cookiecutter(variables=None):
    def _mock_cookiecutter(template_path, output_dir, extra_context, **kwargs):
        template_variables = variables or {}
        create_json_file(Path(template_path) / "cookiecutter.json", template_variables)
        create_toml_file(
            Path(output_dir) / extra_context["output_format"] / "briefcase.toml",
            {"briefcase": {}},
        )

    return _mock_cookiecutter


def test_generate_app(monkeypatch, create_command, myapp, full_context, tmp_path):
    """An app can be generated."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # Mock the contents of the cookiecutter template index
    create_command.tools.cookiecutter.side_effect = mock_cookiecutter(
        {
            "version": "1.2.3",
            "app_name": myapp.app_name,
            "formal_name": myapp.formal_name,
            # Include a "private" cookiecutter variable.
            "_extensions": ["first", "second"],
        }
    )

    # Set an explicit branch
    branch = "some_branch"
    myapp.template_branch = branch
    full_context["template_branch"] = branch

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        str(create_command.data_path / "templates/briefcase-Tester-Dummy-template"),
        no_input=True,
        checkout=branch,
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )

    # The briefcase.toml for the app contains a `context` section that has
    # the intersection of the app's context and
    briefcase_toml = tomllib.loads(
        (tmp_path / "base_path/build/my-app/tester/dummy/briefcase.toml").read_text(
            "utf-8"
        )
    )
    assert briefcase_toml["briefcase"]["python_version"] == platform.python_version()
    assert briefcase_toml["briefcase"]["briefcase_version"] == briefcase.__version__
    assert briefcase_toml["context"] == {
        "version": "1.2.3",
        "app_name": "my-app",
        "formal_name": "My App",
    }


def test_platform_exists(monkeypatch, create_command, myapp, full_context, tmp_path):
    """If the platform directory already exists, it's ok."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"
    full_context["template_branch"] = "v37.42.7"

    # Mock the contents of the cookiecutter template index
    create_command.tools.cookiecutter.side_effect = mock_cookiecutter()

    # Create the build directory
    create_command.build_path(myapp).mkdir(parents=True)

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        str(create_command.data_path / "templates/briefcase-Tester-Dummy-template"),
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


def test_explicit_app_template_hash(
    monkeypatch,
    create_command,
    myapp,
    full_context,
):
    """An explicit app.template_hash overrides the class's default, and is used even
    when the default template and branch are otherwise in effect."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"
    full_context["template_branch"] = "v37.42.7"

    # Mock the contents of the cookiecutter template index
    create_command.tools.cookiecutter.side_effect = mock_cookiecutter()

    # Point the app's template_hash at a *different* hash
    myapp.template_hash = "sha1:0000000000000000000000000000000000000000"

    with pytest.raises(CorruptContentError):
        create_command.generate_app_template(myapp)


def test_custom_template_with_no_hash_does_not_use_class_default(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    tmp_path,
):
    """If a custom template is specified without a template_hash, the class's default
    hash is NOT applied (it belongs to a different template), so no verification is
    attempted, and a warning is logged instead of an error."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"
    full_context["template_branch"] = "v37.42.7"

    # Mock the contents of the cookiecutter template index
    create_command.tools.cookiecutter.side_effect = mock_cookiecutter()

    template = "https://example.com/magic/special-template.git"
    myapp.template = template
    full_context["template_source"] = template

    # Generate the template
    create_command.generate_app_template(myapp)

    create_command.tools.cookiecutter.assert_called_once_with(
        str(create_command.data_path / "templates/special-template"),
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


def test_x_permissions(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    tmp_path,
):
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"
    full_context["template_branch"] = "v37.42.7"

    # Mock the contents of the cookiecutter template index
    create_command.tools.cookiecutter.side_effect = mock_cookiecutter()

    # Define some permissions and requests. The original "permission" and "request"
    # definitions will be hidden from the final template context.

    myapp.permission = {
        # Cross-platform permissions
        "camera": "I need to see you",
        "microphone": "I need to hear you",
        "coarse_location": "I need to know approximately where you are",
        "fine_location": "I need to know exactly where you are",
        "background_location": "I need to know where you are constantly",
        "photo_library": "I need to see your photos",
        # Custom permissions
        "DUMMY_sit": "I can't sit without an invitation",
        "DUMMY.leave.the.dinner.table": "It would be impolite.",
    }
    myapp.request = {"tasty.beverage": True}

    # In the final context, all cross-platform permissions have been converted to upper
    # case, prefixed with "DUMMY", and moved to the `permissions` key. Custom
    # permissions have been moved to the "custom_permissions" key
    full_context["permissions"] = {
        "DUMMY_CAMERA": "I NEED TO SEE YOU",
        "DUMMY_MICROPHONE": "I NEED TO HEAR YOU",
        "DUMMY_COARSE_LOCATION": "I NEED TO KNOW APPROXIMATELY WHERE YOU ARE",
        "DUMMY_FINE_LOCATION": "I NEED TO KNOW EXACTLY WHERE YOU ARE",
        "DUMMY_BACKGROUND_LOCATION": "I NEED TO KNOW WHERE YOU ARE CONSTANTLY",
        "DUMMY_PHOTO_LIBRARY": "I NEED TO SEE YOUR PHOTOS",
    }
    full_context["custom_permissions"] = {
        "DUMMY_sit": "I can't sit without an invitation",
        "DUMMY.leave.the.dinner.table": "It would be impolite.",
    }

    # An extra request has been added because of the camera permission, and the
    # custom request has been preserved.
    full_context["requests"] = {
        "good.lighting": True,
        "tasty.beverage": True,
    }

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        str(create_command.data_path / "templates/briefcase-Tester-Dummy-template"),
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )
