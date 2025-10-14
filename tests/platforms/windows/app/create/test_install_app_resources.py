import pytest

from briefcase.exceptions import BriefcaseCommandError

from .....utils import create_file


def test_minimal_app_resources(create_command, first_app_templated, tmp_path):
    """Windows apps include, at a minimum, a license as extra resources."""
    # Create a license file
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")

    create_command.install_app_resources(first_app_templated)

    # A LICENSE.rtf file has been written.
    assert (tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf").is_file()


def test_post_install_script(create_command, first_app_templated, tmp_path):
    """A post_install script can be provided as extra resources."""
    # Create a license file
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")

    # Create a post-install script
    first_app_templated.post_install_script = "scripts/post_install.bat"
    create_file(tmp_path / "base_path/scripts/post_install.bat", "echo Hello world")

    create_command.install_app_resources(first_app_templated)

    # The post-install script has been written.
    base_path = tmp_path / "base_path/build/first-app/windows/app"
    assert (base_path / "custom_extras/_installer/post_install.bat").is_file()

    # A LICENSE.rtf file has been written.
    assert (tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf").is_file()


def test_non_batch_post_install_script(create_command, first_app_templated, tmp_path):
    """If a post install script isn't a batch file, an error is raised."""
    first_app_templated.post_install_script = "scripts/post_install.sh"
    create_file(tmp_path / "base_path/scripts/post_install.sh", "echo Hello world")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Windows post-install scripts must be .bat files.",
    ):
        create_command.install_app_resources(first_app_templated)


def test_missing_post_install_script(create_command, first_app_templated):
    """If a post install script is specified, but not present, an error is raised."""
    first_app_templated.post_install_script = "scripts/nonexistent.bat"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Couldn't find post-install script scripts/nonexistent.bat",
    ):
        create_command.install_app_resources(first_app_templated)


def test_pre_uninstall_script(create_command, first_app_templated, tmp_path):
    """A pre_uninstall script can be provided as extra resources."""
    # Create a license file
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")

    # Create a post-install script
    first_app_templated.pre_uninstall_script = "scripts/pre_uninstall.bat"
    create_file(tmp_path / "base_path/scripts/pre_uninstall.bat", "echo Hello world")

    create_command.install_app_resources(first_app_templated)

    # The pre-uninstall script has been written.
    base_path = tmp_path / "base_path/build/first-app/windows/app"
    assert (base_path / "custom_extras/_installer/pre_uninstall.bat").is_file()

    # A LICENSE.rtf file has been written.
    assert (tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf").is_file()


def test_non_batch_pre_uninstall_script(create_command, first_app_templated, tmp_path):
    """If a post install script isn't a batch file, an error is raised."""
    first_app_templated.pre_uninstall_script = "scripts/pre_uninstall.sh"
    create_file(tmp_path / "base_path/scripts/pre_uninstall.sh", "echo Goodbye world")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Windows pre-uninstall scripts must be .bat files.",
    ):
        create_command.install_app_resources(first_app_templated)


def test_missing_pre_uninstall_script(create_command, first_app_templated):
    """If a post install script is specified, but not present, an error is raised."""
    first_app_templated.pre_uninstall_script = "scripts/nonexistent.bat"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Couldn't find pre-uninstall script scripts/nonexistent.bat",
    ):
        create_command.install_app_resources(first_app_templated)


def test_alternate_installer_path(create_command, first_app_templated, tmp_path):
    """Windows installer content can be installed in a custom folder."""
    # Define a custom installer path.
    first_app_templated.installer_path = "install_scripts"

    # Create a license file
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")

    # Create a post-install script
    first_app_templated.post_install_script = "scripts/post_install.bat"
    create_file(tmp_path / "base_path/scripts/post_install.bat", "echo Hello world")

    # Create a pre-uninstall script
    first_app_templated.pre_uninstall_script = "scripts/pre_uninstall.bat"
    create_file(tmp_path / "base_path/scripts/pre_uninstall.bat", "echo Goodbye world")

    create_command.install_app_resources(first_app_templated)

    # The post-install script has been written.
    base_path = tmp_path / "base_path/build/first-app/windows/app"
    assert (base_path / "custom_extras/install_scripts/post_install.bat").is_file()

    # The pre-uninstall script has been written.
    assert (base_path / "custom_extras/install_scripts/post_install.bat").is_file()

    # A LICENSE.rtf file has been written.
    assert (base_path / "LICENSE.rtf").is_file()
