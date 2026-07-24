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


@pytest.mark.parametrize(
    ("platform", "arch", "min_os_version", "args"),
    [
        ("macOS", "arm64", None, ["--platform", "macosx_11_0_arm64"]),
        ("macOS", "arm64", "12.3", ["--platform", "macosx_12_3_arm64"]),
        ("macOS", "x86_64", None, ["--platform", "macosx_11_0_x86_64"]),
        ("macOS", "x86_64", "12.3", ["--platform", "macosx_12_3_x86_64"]),
        (
            "iphoneos",
            "arm64",
            None,
            [
                "--platform",
                "ios_13_0_arm64_iphoneos",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
            ],
        ),
        (
            "iphoneos",
            "arm64",
            "16.4",
            [
                "--platform",
                "ios_16_4_arm64_iphoneos",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
            ],
        ),
        (
            "iphonesimulator",
            "arm64",
            None,
            [
                "--platform",
                "ios_13_0_arm64_iphonesimulator",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
            ],
        ),
        (
            "iphonesimulator",
            "arm64",
            "16.4",
            [
                "--platform",
                "ios_16_4_arm64_iphonesimulator",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
            ],
        ),
        ("windows", "x86_64", None, []),
        ("windows", "ARM64", None, []),
        ("linux", "x86_64", None, []),
        ("linux", "aarch64", None, []),
        ("android", "arm64_v8a", None, []),
    ],
)
def test_install_requirements_with_install_path(
    mock_tools,
    mock_venv,
    tmp_path,
    platform,
    arch,
    min_os_version,
    args,
):
    """If an install path is provided, extra platform tags are included."""
    mock_venv.platform = platform
    mock_venv.arch = arch

    mock_venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        install_path=tmp_path / "location",
        min_os_version=min_os_version,
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
            f"--target={tmp_path / 'location'}",
            *args,
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
    )


def test_require_binary(mock_tools, mock_venv):
    """The install can require binary installs."""
    mock_venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        require_binary=True,
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
            "--only-binary",
            ":all:",
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
    )


def test_disable_include_dependencies(mock_tools, mock_venv):
    """Requirements can be installed without dependencies."""
    mock_venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        include_deps=False,
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
            "--no-deps",
            "pkg1",
            "pkg2==1.2.3",
        ],
        check=True,
        encoding="UTF-8",
        env={"VENV": "active"},
    )


def test_extra_installer_args(mock_tools, mock_venv, base_path):
    """Requirements can be installed with extra installer argugments."""
    (base_path / "wheels").mkdir(parents=True)

    mock_venv.install_requirements(
        [
            "pkg1",
            "pkg2==1.2.3",
        ],
        extra_installer_args=["-f", "./wheels"],
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
            "-f",
            "./wheels",
            "pkg1",
            "pkg2==1.2.3",
        ],
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
