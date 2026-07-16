import subprocess
import sys

import pytest

from briefcase.exceptions import RequirementsInstallError


def test_install_requirements(mock_tools, mock_venv):
    """Requirements can be installed with pip."""
    mock_venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        allow_editable=True,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "rewrite",
            mock_venv.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-user",
            "--upgrade",
            "-vv",
            "pkg1",
            "pkg2==1.2.3",
            "-e",
            "../path/to/pkg3",
        ],
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
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
            # Regular packages (should NOT get -e):
            ("package1", False),
            ("package2==1.2.3", False),
            ("package3 == 2.3.4", False),
            ("package4 >= 3.4.5", False),
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
    mock_venv,
    requirement,
    editable,
    allow_editable,
):
    """Test possible path formats that pip supports for editable installation."""
    mock_venv.install_requirements(
        [requirement],
        allow_editable=allow_editable,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "rewrite",
            mock_venv.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-user",
            "--upgrade",
            "-vv",
        ]
        + (["-e", requirement] if (editable and allow_editable) else [requirement]),
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
    )


def test_install_failure(mock_tools, mock_venv):
    """An install failure is reported as a RequirementsInstallError."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="pip", returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        mock_venv.install_requirements(
            ["problem-package"],
            allow_editable=True,
        )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "rewrite",
            mock_venv.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-user",
            "--upgrade",
            "-vv",
            "problem-package",
        ],
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
    )
