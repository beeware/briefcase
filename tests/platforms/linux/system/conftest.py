import pytest

from briefcase.console import Console, Log
from briefcase.platforms.linux.system import LinuxSystemCreateCommand

from ....utils import create_file


@pytest.fixture
def create_command(tmp_path):
    return LinuxSystemCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.fixture
def first_app(first_app_config, tmp_path):
    """A fixture for the first app, rolled out on disk."""
    # Specify a system python app for a dummy vendor
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"

    # Some project-level files.
    create_file(tmp_path / "base_path/LICENSE", "First App License")
    create_file(tmp_path / "base_path/CHANGELOG", "First App Changelog")

    # Make it look like the template has been generated
    bundle_dir = tmp_path / "base_path/build/first-app/somevendor/surprising"

    create_file(bundle_dir / "first-app.1", "First App manpage")

    lib_dir = bundle_dir / "first-app-0.0.1/usr/lib/first-app"
    (lib_dir / "app").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app_packages/firstlib").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app_packages/secondlib").mkdir(parents=True, exist_ok=True)

    # Create some .so files
    # An SO file with different group and world permissions
    (lib_dir / "app/support.so").touch()
    (lib_dir / "app/support.so").chmod(0o775)

    # An SO file with same group and world permissions
    (lib_dir / "app/support_same_perms.so").touch()
    (lib_dir / "app/support_same_perms.so").chmod(0o744)

    # A SO file with both .so and .so.1.0 forms
    (lib_dir / "app_packages/firstlib/first.so").touch()
    (lib_dir / "app_packages/firstlib/first.so.1.0").touch()

    # An SO file with 664 permissions
    (lib_dir / "app_packages/secondlib/second_a.so").touch()
    (lib_dir / "app_packages/secondlib/second_a.so").chmod(0o664)

    (lib_dir / "app_packages/secondlib/second_b.so").touch()

    return first_app_config
