from pathlib import Path
from unittest.mock import MagicMock

import pytest

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
    command.tools[first_app_generated].app_context = command.tools.subprocess
    return command


def test_shared_requirements(command, first_app_generated):
    """Identical files are shared; ABI-specific dependency contents stay separate."""
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
