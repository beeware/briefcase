from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import briefcase.platforms.macOS.__init__ as mac_mod


@pytest.fixture
def pkg_dummy(tmp_path):
    """Minimal 'self' object for macOSPackageMixin path helpers."""
    dist = tmp_path / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    class Dummy:
        dist_path: Path = dist
        base_path: Path = tmp_path

        def package_path(self, app):
            # Mimic the usual build layout used elsewhere in tests
            return (
                self.base_path
                / "build"
                / app.app_name
                / "macos"
                / "app"
                / f"{app.formal_name}.app"
            )

        def distribution_path(self, app):
            if app.packaging_format == "zip":
                return self.dist_path / f"{app.formal_name}-{app.version}.app.zip"
            elif app.packaging_format == "pkg":
                return self.dist_path / f"{app.formal_name}-{app.version}.pkg"
            else:
                return self.dist_path / f"{app.formal_name}-{app.version}.dmg"

    return Dummy()


def _app(
    fmt: str,
    formal_name: str = "First App",
    app_name: str = "first-app",
    version: str = "1.2.3",
):
    return SimpleNamespace(
        app_name=app_name,
        formal_name=formal_name,
        version=version,
        packaging_format=fmt,
    )


def test_notarization_path_uses_package_path_for_zip(pkg_dummy):
    app = _app("zip")

    got = mac_mod.macOSPackageMixin.notarization_path(pkg_dummy, app)
    want = pkg_dummy.package_path(app)

    assert got == want
    assert got.name.endswith(".app")


def test_notarization_path_uses_distribution_for_pkg_and_dmg(pkg_dummy):
    app_pkg = _app("pkg")
    app_dmg = _app("dmg")

    got_pkg = mac_mod.macOSPackageMixin.notarization_path(pkg_dummy, app_pkg)
    assert got_pkg == mac_mod.macOSPackageMixin.distribution_path(pkg_dummy, app_pkg)
    assert got_pkg == pkg_dummy.dist_path / "First App-1.2.3.pkg"

    got_dmg = mac_mod.macOSPackageMixin.notarization_path(pkg_dummy, app_dmg)
    assert got_dmg == mac_mod.macOSPackageMixin.distribution_path(pkg_dummy, app_dmg)
    assert got_dmg == pkg_dummy.dist_path / "First App-1.2.3.dmg"


def test_distribution_path_variants(pkg_dummy):
    app_zip = _app("zip")
    app_pkg = _app("pkg")
    app_dmg = _app("dmg")

    assert (
        mac_mod.macOSPackageMixin.distribution_path(pkg_dummy, app_zip)
        == pkg_dummy.dist_path / "First App-1.2.3.app.zip"
    )
    assert (
        mac_mod.macOSPackageMixin.distribution_path(pkg_dummy, app_pkg)
        == pkg_dummy.dist_path / "First App-1.2.3.pkg"
    )
    assert (
        mac_mod.macOSPackageMixin.distribution_path(pkg_dummy, app_dmg)
        == pkg_dummy.dist_path / "First App-1.2.3.dmg"
    )
