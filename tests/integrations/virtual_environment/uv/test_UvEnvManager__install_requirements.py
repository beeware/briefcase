import os
import subprocess
import sys

import pytest

from briefcase.exceptions import RequirementsInstallError


def test_install_requirements(mock_tools, venv):
    """Requirements can be installed with `uv pip install`."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
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
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
        ]
        + (["-e", requirement] if (editable and allow_editable) else [requirement]),
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )


@pytest.mark.parametrize(
    ("platform", "arch", "min_os_version", "args", "extra_env"),
    [
        ("macOS", "arm64", None, ["--python-platform", "aarch64-apple-darwin"], {}),
        (
            "macOS",
            "arm64",
            "12.3",
            ["--python-platform", "aarch64-apple-darwin"],
            {"MACOSX_DEPLOYMENT_TARGET": "12.3"},
        ),
        ("macOS", "x86_64", None, ["--python-platform", "x86_64-apple-darwin"], {}),
        (
            "macOS",
            "x86_64",
            "12.3",
            ["--python-platform", "x86_64-apple-darwin"],
            {"MACOSX_DEPLOYMENT_TARGET": "12.3"},
        ),
        ("windows", "AMD64", None, [], {}),
        ("windows", "ARM64", None, [], {}),
        ("linux", "x86_64", None, [], {}),
        ("linux", "aarch4", None, [], {}),
    ],
)
def test_install_requirements_with_install_path(
    mock_tools,
    venv,
    tmp_path,
    platform,
    arch,
    min_os_version,
    args,
    extra_env,
):
    """If an install path is provided, extra platform tags are included."""
    venv.platform = platform
    venv.arch = arch

    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        install_path=tmp_path / "location",
        min_os_version=min_os_version,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            f"--target={tmp_path / 'location'}",
            *args,
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
            **extra_env,
        },
    )


def test_require_binary(mock_tools, venv):
    """The install can require binary installs."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        require_binary=True,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "--only-binary",
            ":all:",
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )


def test_require_binaries_with_source(mock_tools, venv):
    """If there are source dependencies, require_binary is ignored."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        require_binary=True,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )


def test_disable_include_dependencies(mock_tools, venv):
    """Requirements can be installed without dependencies."""
    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        include_deps=False,
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "--no-deps",
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )


def test_extra_installer_args(mock_tools, venv, base_path):
    """Requirements can be installed with extra installer argugments."""
    (base_path / "wheels").mkdir(parents=True)

    venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        extra_installer_args=["-f", "./wheels"],
    )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "-f",
            base_path / "wheels",
            "pkg1",
            "pkg2==1.2.3",
            "../path/to/pkg3",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )


def test_install_failure(mock_tools, venv):
    """An install failure is reported as a RequirementsInstallError."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="pip", returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        venv.install_requirements(
            ["problem-package"],
            allow_editable=True,
        )

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "uv",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "problem-package",
        ],
        check=True,
        encoding="UTF-8",
        env={
            "PATH": str(venv.bin_dir) + os.pathsep + os.environ["PATH"],
            "VIRTUAL_ENV": str(venv.venv_path),
        },
    )
