import sys

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


def test_requires_python_met(base_command, my_app):
    """Validation passes if requires-python specifies a version lower than the running interpreter."""

    major, minor, micro, *_ = sys.version_info
    spec = f">{major}.{minor - 1}.{micro}"
    base_command.global_config = _get_global_config(requires_python=spec)
    base_command.verify_required_python(my_app)


def test_requires_python_unmet(base_command, my_app):
    """Validation fails if requires-python specifies a version greater than the running interpreter."""

    major, minor, micro, *_ = sys.version_info
    spec = f">{major}.{minor + 1}.{micro}"
    base_command.global_config = _get_global_config(requires_python=spec)

    with pytest.raises(UnsupportedPythonVersion):
        base_command.verify_required_python(my_app)


def test_requires_python_invalid_specifier(base_command, my_app):
    """Validation fails if requires-python is not a valid specifier."""

    base_command.global_config = _get_global_config(requires_python="0")

    with pytest.raises(BriefcaseConfigError, match="Invalid requires-python"):
        base_command.verify_required_python(my_app)
