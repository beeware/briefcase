from pathlib import Path

import briefcase

from ...utils import create_toml_file


def test_context_unchanged(base_command, my_app, capsys):
    """If all the template context variables are the same, return False."""

    create_toml_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        {
            "briefcase": {
                "python_version": base_command.tools.platform.python_version(),
                "briefcase_version": briefcase.__version__,
            },
            "context": {
                "version": "1.2.3",
                "app_name": "my-app",
                "formal_name": "My App",
                "info": {},
                "entitlements": {"value1": 1, "value2": 2},
            },
        },
    )

    # Add in some complex values to the current context
    my_app.info = {}
    my_app.entitlements = {"value1": 1, "value2": 2}

    assert not base_command.app_context_changed(my_app)

    assert capsys.readouterr().out == ""


def test_context_changed(base_command, my_app, capsys):
    """If any context variables have changed, return True and output a warning."""

    create_toml_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        {
            "briefcase": {
                "python_version": base_command.tools.platform.python_version(),
                "briefcase_version": briefcase.__version__,
            },
            "context": {
                "version": "1.2.2",
                "app_name": "old-name",
                "formal_name": "My App",
                "info": {},
                "entitlements": {"value1": 1, "value2": 2},
            },
        },
    )

    # Add in some complex values to the current context
    my_app.info = {}
    my_app.entitlements = {"value1": 1, "value2": 3, "other": "new"}

    assert base_command.app_context_changed(my_app)

    stdout = capsys.readouterr().out
    assert "Value for 'version' has changed (was: '1.2.2'; now '1.2.3')" in stdout
    assert "Value for 'app_name' has changed (was: 'old-name'; now 'my-app')" in stdout
    assert (
        "Value for 'entitlements' has changed "
        "(was: {'value1': 1, 'value2': 2}; "
        "now {'value1': 1, 'value2': 3, 'other': 'new'})"
    ) in stdout


def test_context_variable_missing(base_command, my_app, capsys):
    """If the generated template required a variable that is no longer there,
    return True and output a warning."""

    create_toml_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        {
            "briefcase": {
                "python_version": base_command.tools.platform.python_version(),
                "briefcase_version": briefcase.__version__,
            },
            "context": {
                "version": "1.2.3",
                "app_name": "my-app",
                "formal_name": "My App",
                "info": {},
                "entitlements": {"value1": 1, "value2": 2},
                "no_longer_present": "historical",
            },
        },
    )

    # Add in some complex values to the current context
    my_app.entitlements = {"value1": 1, "value2": 2}

    assert base_command.app_context_changed(my_app)

    stdout = capsys.readouterr().out
    assert "App no longer has a value for 'no_longer_present'" in stdout
    assert "App no longer has a value for 'info'" in stdout


def test_no_template_context(base_command, my_app, capsys):
    """If the generated template didn't preserve template context, output a
    warning and return True."""

    create_toml_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        {
            "briefcase": {
                "python_version": base_command.tools.platform.python_version(),
                "briefcase_version": briefcase.__version__,
            },
        },
    )

    assert base_command.app_context_changed(my_app)

    stdout = capsys.readouterr().out
    assert "App did not preserve template context on generation" in stdout


def test_toml_safety(base_command, my_app, capsys):
    """TOML-unsafe values can round trip."""

    create_toml_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        {
            "briefcase": {
                "python_version": base_command.tools.platform.python_version(),
                "briefcase_version": briefcase.__version__,
            },
            "context": {
                "version": "1.2.3",
                "app_name": "my-app",
                "formal_name": "My App",
                "is_none": "<::NONE::>",
                "list_value": ["<::NONE::>", 2, 3],
                "dict_value": {
                    "value1": ["<::NONE::>", 5, 6],
                    "value2": "<::NONE::>",
                    "value3": "/path/to/deep_file.txt",
                },
                "path_value": "/path/to/file.txt",
            },
        },
    )

    # Add in some complex values to the current context
    my_app.is_none = None
    my_app.list_value = [None, 2, 3]
    my_app.dict_value = {
        "value1": [None, 5, 6],
        "value2": None,
        "value3": Path("/path/to/deep_file.txt"),
    }
    my_app.path_value = Path("/path/to/file.txt")

    assert not base_command.app_context_changed(my_app)

    assert capsys.readouterr().out == ""
