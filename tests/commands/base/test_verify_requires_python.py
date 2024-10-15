import platform
from unittest import mock

import pytest

from briefcase.config import GlobalConfig
from briefcase.exceptions import BriefcaseConfigError, UnsupportedPythonVersion


def _get_global_config(requires_python):
    return GlobalConfig(
        project_name="pep621-requires-python-testing",
        version="0.0.1",
        bundle="com.example",
        requires_python=requires_python,
    )


def test_no_requires_python(base_command, my_app):
    """If requires-python isn't set, no verification is necessary."""

    base_command.global_config = _get_global_config(requires_python=None)
    base_command.verify_required_python(my_app)


@pytest.mark.parametrize(
    "requires_python",
    (
        "!= 3.2",
        ">= 3.2",
        "> 3.2",
        ">= {current}",
        "== {current}",
        "~= {current}",
        "<= {current}",
        "< 3.100",
    ),
)
def test_requires_python_met(base_command, my_app, requires_python):
    """Validation passes if requires-python specifies a version compatible with the running interpreter."""

    base_command.global_config = _get_global_config(
        requires_python.format(current=platform.python_version())
    )
    base_command.verify_required_python(my_app)


@pytest.mark.parametrize(
    "requires_python",
    [
        # Require a version higher than anything that can exist
        "> 3.100",
        ">= 3.100",
        # Require a version lower than anything that is supported
        "< 3.2",
        "<= 3.2",
        # Equality with a version that definitely isn't supported
        "== 2.0",
        "~= 2.0",
    ],
)
def test_requires_python_unmet(base_command, my_app, requires_python):
    """Validation fails if requires-python specifies a version incompatible with the running interpreter."""

    base_command.global_config = _get_global_config(requires_python)

    with pytest.raises(UnsupportedPythonVersion):
        base_command.verify_required_python(my_app)


def test_requires_python_invalid_specifier(base_command, my_app):
    """Validation fails if requires-python is not a valid specifier."""

    base_command.global_config = _get_global_config(requires_python="0")

    with pytest.raises(BriefcaseConfigError, match="Invalid requires-python"):
        base_command.verify_required_python(my_app)


@mock.patch("platform.python_version")
def test_requires_python_prerelease(python_version_mock, base_command, my_app):
    """Verify that pre-release Python versions are included in matches."""
    python_version_mock.return_value = "3.14.0a0"

    base_command.global_config = _get_global_config(requires_python=">=3.12")
    base_command.verify_required_python(my_app)
