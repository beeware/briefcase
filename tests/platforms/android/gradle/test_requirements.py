import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.debuggers.base import BaseDebugger
from briefcase.exceptions import RequirementsInstallError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import GradleCreateCommand, GradleUpdateCommand

from ....utils import create_file


@pytest.fixture(params=[GradleCreateCommand, GradleUpdateCommand])
def command(request, dummy_console, tmp_path, first_app_generated):
    command = request.param(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.sys = MagicMock(spec_set=sys)
    command.tools.sys.version_info = (3, 13, 0)
    command.tools[first_app_generated].app_context = command.tools.subprocess
    return command


@pytest.mark.parametrize("version", [(3, 11, 9), (3, 12, 10), (3, 13, 0)])
def test_shared_requirements(command, first_app_generated, version):
    """Identical files are shared; ABI-specific dependency contents stay separate."""
    command.tools.sys.version_info = version
    first_app_generated.requires = ["example==1.2.3"]

    def install(args, **kwargs):
        if "install" in args:
            target = Path(
                next(arg[9:] for arg in args if str(arg).startswith("--target="))
            )
            create_file(target / "example/__init__.py", "# Shared Python code")
            create_file(target / "example/native.so", target.name)

    command.tools.subprocess.run.side_effect = install
    venv = command.create_app_environment(
        first_app_generated,
        platform="android",
        arch="arm64",
    )
    command.install_app_requirements(first_app_generated, venv)

    packages_path = command.app_packages_path(first_app_generated)
    assert (packages_path / "common/example/__init__.py").read_text(
        encoding="utf-8"
    ) == "# Shared Python code"
    for abi in ["arm64-v8a", "x86_64"]:
        assert not (packages_path / abi / "example/__init__.py").exists()
        assert (packages_path / abi / "example/native.so").read_text(
            encoding="utf-8"
        ) == abi


@pytest.mark.parametrize("requires", [[], ["replacement==2.0"]])
def test_removed_requirements(command, first_app_generated, requires):
    """Updating requirements removes old packages, including removed ABIs."""
    packages_path = command.app_packages_path(first_app_generated)
    create_file(packages_path / "common/old.py", "old dependency")
    create_file(packages_path / "arm64-v8a/old.so", "old binary")
    create_file(packages_path / "x86_64/old.so", "removed ABI")
    first_app_generated.android_abis = ["arm64-v8a"]
    first_app_generated.requires = requires
    venv = command.create_app_environment(
        first_app_generated,
        platform="android",
        arch="arm64",
    )

    command.install_app_requirements(first_app_generated, venv)

    assert (packages_path / "common").is_dir()
    assert (packages_path / "arm64-v8a").is_dir()
    assert not (packages_path / "common/old.py").exists()
    assert not (packages_path / "arm64-v8a/old.so").exists()
    assert not (packages_path / "x86_64").exists()


def test_test_and_debugger_requirements(command, first_app_generated):
    """Test and debugger dependencies are installed for every configured ABI."""
    first_app_generated.requires = ["example"]
    first_app_generated.test_mode = True
    first_app_generated.test_requires = ["pytest"]
    first_app_generated.debugger = MagicMock(spec_set=BaseDebugger)
    first_app_generated.debugger.debugger_support_pkg = "debug-support"
    first_app_generated.min_os_version = "28"
    venv = command.create_app_environment(
        first_app_generated,
        platform="android",
        arch="arm64",
    )

    command.install_app_requirements(first_app_generated, venv)

    installs = [
        call.args[0]
        for call in command.tools.subprocess.run.call_args_list
        if "install" in call.args[0]
    ]
    assert len(installs) == 2
    for args in installs:
        assert args[-3:] == ["example", "pytest", "debug-support"]
        assert args[args.index("--platform") + 1].startswith("android_28_")


def test_install_failure(command, first_app_generated):
    """Installation failures identify the ABI whose wheels could not be installed."""
    first_app_generated.requires = ["example"]

    def fail_install(args, **kwargs):
        if "install" in args and "android_24_x86_64" in args:
            raise subprocess.CalledProcessError(1, args)

    command.tools.subprocess.run.side_effect = fail_install
    venv = command.create_app_environment(
        first_app_generated,
        platform="android",
        arch="arm64",
    )

    with pytest.raises(
        RequirementsInstallError,
        match="Android wheels are available for x86_64",
    ):
        command.install_app_requirements(first_app_generated, venv)


def test_single_abi(command, first_app_generated):
    """A single-ABI app installs only that ABI and exposes its files in common."""
    first_app_generated.requires = ["example"]
    first_app_generated.android_abis = ["x86_64"]

    def install(args, **kwargs):
        if "install" in args:
            target = Path(
                next(arg[9:] for arg in args if str(arg).startswith("--target="))
            )
            create_file(target / "example.py", "# Installed for x86_64")

    command.tools.subprocess.run.side_effect = install
    venv = command.create_app_environment(
        first_app_generated,
        platform="android",
        arch="arm64",
    )

    command.install_app_requirements(first_app_generated, venv)

    packages_path = command.app_packages_path(first_app_generated)
    assert (packages_path / "common/example.py").is_file()
    assert (packages_path / "x86_64").is_dir()
    assert not (packages_path / "arm64-v8a").exists()
    assert (
        sum(
            "install" in call.args[0]
            for call in command.tools.subprocess.run.call_args_list
        )
        == 1
    )
