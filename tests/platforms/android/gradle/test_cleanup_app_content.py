import pytest

from briefcase.platforms.android.gradle import GradleCreateCommand, GradleUpdateCommand

from ....utils import create_file


@pytest.fixture(params=[GradleCreateCommand, GradleUpdateCommand])
def command(request, dummy_console, tmp_path):
    return request.param(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("custom_cleanup", [False, True])
def test_keep_chaquopy_pycache(command, first_app_generated, custom_cleanup):
    """Android cleanup preserves Chaquopy's bytecode without skipping custom cleanup."""
    bundle_path = command.bundle_path(first_app_generated)
    pyc_path = (
        bundle_path / "build/chaquopy/bp/lib/site-packages/pip/__pycache__/main.pyc"
    )
    create_file(pyc_path, "cached pip bytecode")
    timestamp = pyc_path.stat().st_mtime_ns

    unwanted_path = bundle_path / "app/unwanted.txt"
    create_file(unwanted_path, "remove by request")
    if custom_cleanup:
        first_app_generated.cleanup_paths = ["app/unwanted.txt"]

    command.cleanup_app_content(first_app_generated)

    assert pyc_path.read_text(encoding="utf-8") == "cached pip bytecode"
    assert pyc_path.stat().st_mtime_ns == timestamp
    assert unwanted_path.exists() is not custom_cleanup


def test_explicit_pycache_cleanup(command, first_app_generated):
    """An explicit cleanup pattern can still remove bytecode on Android."""
    bundle_path = command.bundle_path(first_app_generated)
    pyc_path = bundle_path / "app/__pycache__/main.pyc"
    create_file(pyc_path, "app bytecode")
    first_app_generated.cleanup_paths = ["app/__pycache__"]

    command.cleanup_app_content(first_app_generated)

    assert not pyc_path.parent.exists()
