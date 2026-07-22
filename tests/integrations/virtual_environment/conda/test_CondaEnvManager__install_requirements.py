import subprocess
import sys
from unittest.mock import call

import pytest

from briefcase.exceptions import RequirementsInstallError


@pytest.mark.parametrize("verbose", [True, False])
def test_install_requirements(mock_tools, venv, verbose, tmp_path):
    """Requirements are installed with `conda install`."""
    mock_tools.console.is_verbose = verbose

    venv.install_requirements(
        [
            "pkg1",
            "pkg2=1.2.3",
        ],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "install",
            "--prefix",
            venv.venv_path,
            "--yes",
        ]
        + ([] if verbose else ["--quiet"])
        + [
            "pkg1",
            "pkg2=1.2.3",
        ],
        check=True,
    )


@pytest.mark.parametrize(
    ("requirement", "editable"),
    (
        [
            # Relative paths and single level
            ("./current-dir", True),
            ("../parent-dir", True),
            # Relative paths and multiple levels
            ("../../grandparent/package", True),
            ("./deeply/nested/package", True),
            ("../sibling/package", True),
            # Simple relative paths
            ("folder/package", True),
            ("src/mypackage", True),
            # Absolute paths
            ("/absolute/path", True),
            # SCM URLs (should NOT get -e for now):
            ("git+https://github.com/user/repo.git", False),
            ("git+ssh://git@github.com/user/repo.git", False),
            ("hg+https://bitbucket.org/user/repo", False),
            ("git+https://github.com/user/repo.git@1.2.3", False),
            ("SomeProject@git+https://github.com/user/repo.git", False),
            ("SomeProject@git+https://github.com/user/repo.git@branch", False),
            (
                "SomeProject@git+https://github.com/user/repo.git#subdirectory=sub_dir",
                False,
            ),
            # Archives (should NOT get -e):
            ("./local/package.tar.gz", False),
            ("./local/package.zip", False),
            ("./local/package.whl", False),
            ("./local/package.tar.bz2", False),
            ("./local/package.tar", False),
            # Archives specified by URL
            ("https://github.com/user/repo/archive/main.tar.gz", False),
            ("SomeProject@https://github.com/user/repo/archive/main.tar.gz", False),
            ("https://files.pythonhosted.org/packages/.../package-1.0.tar.gz", False),
        ]
        + (
            [
                # Windows paths. Windows honors unix-style paths, but on Unix,
                # windows-style paths appear as package names, so we only test
                # this option on Windows.
                ("folder\\windows", True),
                (".\\windows\\current", True),
                ("..\\windows\\parent", True),
                ("C:\\absolute\\windows", True),
            ]
            if sys.platform == "win32"
            else []
        )
    ),
)
@pytest.mark.parametrize("allow_editable", [True, False])
def test_install_requirements_path_formats(
    mock_tools,
    venv,
    requirement,
    editable,
    allow_editable,
):
    """Test possible path formats that uv supports for editable installation."""
    venv.install_requirements(
        [requirement],
        allow_editable=allow_editable,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "run",
            "--prefix",
            venv.venv_path,
            "--no-capture-output",
            "pip",
            "install",
            "--only-binary",
            ":all:",
        ]
        + (["-e", requirement] if (editable and allow_editable) else [requirement]),
        check=True,
        env={"PIP_REQUIRE_VIRTUALENV": None},
    )


def test_install_mixed_requirements(mock_tools, venv, tmp_path):
    """A mix of conda and local file requirements requires 2 installs."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2=1.2.3",
            "../path/to/pkg3",
        ],
    )

    # Two install calls required - one to Conda, and one to pip (to install local packages)
    assert mock_tools.subprocess.run.mock_calls == [
        call(
            [
                "conda",
                "install",
                "--prefix",
                venv.venv_path,
                "--yes",
                "pkg1",
                "pkg2=1.2.3",
            ],
            check=True,
        ),
        call(
            [
                "conda",
                "run",
                "--prefix",
                venv.venv_path,
                "--no-capture-output",
                "pip",
                "install",
                "--only-binary",
                ":all:",
                "../path/to/pkg3",
            ],
            check=True,
            env={"PIP_REQUIRE_VIRTUALENV": None},
        ),
    ]


def test_disable_include_dependencies(mock_tools, venv, tmp_path):
    """Requirements can be installed without dependencies."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2=1.2.3",
            "../path/to/pkg3",
        ],
        include_deps=False,
    )

    # Two install calls required - one to Conda, and one to pip (to install local packages)
    assert mock_tools.subprocess.run.mock_calls == [
        call(
            [
                "conda",
                "install",
                "--prefix",
                venv.venv_path,
                "--yes",
                "--no-deps",
                "pkg1",
                "pkg2=1.2.3",
            ],
            check=True,
        ),
        call(
            [
                "conda",
                "run",
                "--prefix",
                venv.venv_path,
                "--no-capture-output",
                "pip",
                "install",
                "--only-binary",
                ":all:",
                "--no-deps",
                "../path/to/pkg3",
            ],
            check=True,
            env={"PIP_REQUIRE_VIRTUALENV": None},
        ),
    ]


def test_extra_installer_args(mock_tools, venv):
    """Additional installer arguments are appended to the command."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2=1.2.3",
        ],
        extra_installer_args=["--channel", "conda-forge"],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "install",
            "--prefix",
            venv.venv_path,
            "--yes",
            "--channel",
            "conda-forge",
            "pkg1",
            "pkg2=1.2.3",
        ],
        check=True,
    )


@pytest.mark.parametrize("requires", [[], None])
def test_install_no_requirements(mock_tools, venv, requires):
    """If there are no requirements, conda is not invoked."""
    venv.install_requirements(requires)

    mock_tools.subprocess.run.assert_not_called()


def test_install_failure(mock_tools, venv):
    """An install failure is reported as a RequirementsInstallError."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="conda", returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        venv.install_requirements(["problem-package"])

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "install",
            "--prefix",
            venv.venv_path,
            "--yes",
            "problem-package",
        ],
        check=True,
    )


def test_pip_install_failure(mock_tools, venv):
    """An install failure in a local file is reported as a RequirementsInstallError."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="conda", returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        venv.install_requirements(["../problem-package"])

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "run",
            "--prefix",
            venv.venv_path,
            "--no-capture-output",
            "pip",
            "install",
            "--only-binary",
            ":all:",
            "../problem-package",
        ],
        check=True,
        env={"PIP_REQUIRE_VIRTUALENV": None},
    )
