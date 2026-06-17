import subprocess

import pytest

from briefcase.exceptions import RequirementsInstallError


@pytest.mark.parametrize("verbose", [True, False])
def test_install_requirements(mock_tools, venv, verbose):
    """Requirements are installed with `pixi install`."""
    mock_tools.console.is_verbose = verbose

    venv.install_requirements(
        [
            "pkg1",
            "pkg2=1.2.3",
            "pkg3>=2.0",
        ],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "pixi",
            "add",
            "--manifest-path",
            venv.venv_path,
            "pkg1",
            "pkg2=1.2.3",
            "pkg3>=2.0",
        ],
        check=True,
    )


def test_install_requirements_with_installer_args(mock_tools, venv):
    """Additional installer arguments are appended to the command."""
    venv.install_requirements(
        ["pkg1"],
        installer_args=["--channel", "pixi-forge"],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "pixi",
            "add",
            "--manifest-path",
            venv.venv_path,
            "--channel",
            "pixi-forge",
            "pkg1",
        ],
        check=True,
    )


def test_install_requirements_editable_ignored(mock_tools, venv):
    """`allow_editable` has no effect; requirements are passed through verbatim."""
    venv.install_requirements(
        ["../path/to/pkg"],
        allow_editable=True,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "pixi",
            "add",
            "--manifest-path",
            venv.venv_path,
            "../path/to/pkg",
        ],
        check=True,
    )


@pytest.mark.parametrize("requires", [[], None])
def test_install_no_requirements(mock_tools, venv, requires):
    """If there are no requirements, pixi is not invoked."""
    venv.install_requirements(requires)

    mock_tools.subprocess.run.assert_not_called()


def test_install_failure(mock_tools, venv):
    """An install failure is reported as a RequirementsInstallError."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="pixi", returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        venv.install_requirements(["problem-package"])

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "pixi",
            "add",
            "--manifest-path",
            venv.venv_path,
            "problem-package",
        ],
        check=True,
    )
