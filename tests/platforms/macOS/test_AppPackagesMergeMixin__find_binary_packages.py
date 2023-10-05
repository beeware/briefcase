from ...utils import create_installed_package


def test_find_binary_packages(dummy_command, tmp_path):
    """Binary packages can be identified in a app-packages folder."""

    create_installed_package(
        tmp_path / "app-packages",
        "pure-package1",
        version="1.2.3",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "pure-package2",
        version="1.2.4",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "universal-package-1",
        version="2.3.4",
        tag="macOS_11_universal2",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "universal-package-2",
        version="2.3.5",
        tag="macOS_13_universal2",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "binary-package-1",
        version="3.4.5",
        tag="macOS_11_arm64",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "binary-package-2",
        version="3.4.6",
        tag="macOS_13_arm64",
    )

    binary_packages = dummy_command.find_binary_packages(
        tmp_path / "app-packages",
        universal_suffix="_universal2",
    )

    # Binary wheels are discovered. We don't care about the order they are returned in,
    # just that they're all found.
    assert len(binary_packages) == 2
    assert set(binary_packages) == {
        ("binary-package-1", "3.4.5"),
        ("binary-package-2", "3.4.6"),
    }


def test_find_binary_packages_non_universal(dummy_command, tmp_path):
    """If no universal wheel format is specified, universal wheels are identified as
    binary."""

    create_installed_package(
        tmp_path / "app-packages",
        "pure-package1",
        version="1.2.3",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "pure-package2",
        version="1.2.4",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "universal-package-1",
        version="2.3.4",
        tag="macOS_11_universal2",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "universal-package-2",
        version="2.3.5",
        tag="macOS_13_universal2",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "binary-package-1",
        version="3.4.5",
        tag="macOS_11_arm64",
    )
    create_installed_package(
        tmp_path / "app-packages",
        "binary-package-2",
        version="3.4.6",
        tag="macOS_13_arm64",
    )

    binary_packages = dummy_command.find_binary_packages(tmp_path / "app-packages")

    # Binary wheels are discovered. We don't care about the order they are returned in,
    # just that they're all found.
    assert len(binary_packages) == 4
    assert set(binary_packages) == {
        ("universal-package-1", "2.3.4"),
        ("universal-package-2", "2.3.5"),
        ("binary-package-1", "3.4.5"),
        ("binary-package-2", "3.4.6"),
    }
