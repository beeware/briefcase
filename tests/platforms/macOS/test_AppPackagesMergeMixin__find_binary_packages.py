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
        extra_content=[
            # A vendored, but incomplete .dist-info folder. See #1970
            ("vendored/nested-incomplete.dist-info/LICENSE", "Nested License", 0o644),
        ],
    )
    # A vendored .dist-info folder. This *isn't* found and processed.
    create_installed_package(
        tmp_path / "app-packages/binary-package-2/vendored",
        "nested-package",
        version="9.9.9",
        tag="macOS_13_arm64",
    )
    # Packages with multiple binary tags (see #2690)
    # Multiple tags, where universal2 duplicates explicit tagging
    create_installed_package(
        tmp_path / "app-packages",
        "multi-tagged-binary-package-1",
        version="3.4.7",
        tag=["macOS_11_x86-64", "macOS_11_arm64", "macOS_11_universal2"],
    )
    # Universal2 even though it isn't tagged as such
    create_installed_package(
        tmp_path / "app-packages",
        "multi-tagged-binary-package-2",
        version="3.4.8",
        tag=["macOS_11_x86-64", "macOS_11_arm64"],
    )
    # Multiple tagged, but not a universal pair
    create_installed_package(
        tmp_path / "app-packages",
        "multi-tagged-binary-package-3",
        version="3.4.9",
        tag=["macOS_11_arm64", "macOS_11_ppc"],
    )
    # Multiple tagged, includes universal and host, but *not* other
    create_installed_package(
        tmp_path / "app-packages",
        "multi-tagged-binary-package-4",
        version="3.4.10",
        tag=["macOS_11_arm64", "macOS_11_universal2"],
    )
    # Multiple tagged, includes universal and other, but *not* host
    create_installed_package(
        tmp_path / "app-packages",
        "multi-tagged-binary-package-5",
        version="3.4.11",
        tag=["macOS_11_x86_64", "macOS_11_universal2"],
    )

    binary_packages = dummy_command.find_binary_packages(
        tmp_path / "app-packages",
        universal_suffix="_universal2",
        other_suffix="_x86-64",
    )

    # Binary wheels are discovered. We don't care about the order they are returned in,
    # just that they're all found.
    assert set(binary_packages) == {
        ("binary-package-1", "3.4.5"),
        ("binary-package-2", "3.4.6"),
        ("multi-tagged-binary-package-3", "3.4.9"),
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
