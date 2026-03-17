from __future__ import annotations

import subprocess
import tarfile
from pathlib import Path

from briefcase.commands.convert import find_changelog_filename
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats.base import BasePackagingFormat


def debian_multiline_description(description):
    """Generate a Debian multiline description string.

    The long description in a Debian control file must *not* contain any blank lines,
    and each line must start with a single space. Convert a long description into Debian
    format.

    :param description: A multi-line long description string.
    :returns: A string in Debian's multiline format
    """
    return "\n ".join(line for line in description.split("\n") if line.strip() != "")


class LinuxAppImagePackagingFormat(BasePackagingFormat):
    @property
    def name(self) -> str:
        return "appimage"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / self.command.binary_name(app)

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info("Packaging AppImage...", prefix=app.app_name)
        with self.command.console.wait_bar("Packing..."):
            self.command.tools.shutil.copy(
                self.command.binary_path(app),
                self.distribution_path(app),
            )

    def priority(self, app: AppConfig) -> int:
        return 10


class LinuxFlatpakPackagingFormat(BasePackagingFormat):
    @property
    def name(self) -> str:
        return "flatpak"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.flatpak"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info("Building bundle...", prefix=app.app_name)
        with self.command.console.wait_bar("Bundling..."):
            _, flatpak_repo_url = self.command.flatpak_runtime_repo(app)
            self.command.tools.flatpak.bundle(
                repo_url=flatpak_repo_url,
                bundle_identifier=app.bundle_identifier,
                app_name=app.app_name,
                version=app.version,
                build_path=self.command.bundle_path(app),
                output_path=self.distribution_path(app),
            )

    def priority(self, app: AppConfig) -> int:
        return 10


class LinuxSystemPackagingFormat(BasePackagingFormat):
    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / self.command.distribution_filename(app)

    def priority(self, app: AppConfig) -> int:
        # System packages are preferred if they match the host vendor
        if app.target_vendor_base == {
            "deb": "debian",
            "rpm": "rhel",  # or suse
            "pkg": "arch",
        }.get(self.name):
            return 10
        # SUSE also uses RPM
        if self.name == "rpm" and app.target_vendor_base == "suse":
            return 10
        return 1


class LinuxDebPackagingFormat(LinuxSystemPackagingFormat):
    @property
    def name(self) -> str:
        return "deb"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info("Building .deb package...", prefix=app.app_name)

        # The long description *must* exist.
        if app.long_description is None:
            raise BriefcaseCommandError(
                "App configuration does not define `long_description`. "
                "Debian projects require a long description."
            )

        # Write the Debian metadata control file.
        with self.command.console.wait_bar("Write Debian package control file..."):
            DEBIAN_path = self.command.package_path(app) / "DEBIAN"

            if DEBIAN_path.exists():
                self.command.tools.shutil.rmtree(DEBIAN_path)

            DEBIAN_path.mkdir()
            # dpkg-dep requires "DEBIAN" directory is >=0755 and <=0775
            DEBIAN_path.chmod(0o755)

            # Add runtime package dependencies. App config has been finalized,
            # so this will be the target-specific definition, if one exists.
            # libc6 is added because lintian complains without it, even though
            # it's a dependency of the thing we *do* care about - python.
            system_runtime_requires = ", ".join(
                [
                    f"libc6 (>={app.glibc_version})",
                    f"libpython{app.python_version_tag}",
                    *getattr(app, "system_runtime_requires", []),
                ]
            )

            with (DEBIAN_path / "control").open("w", encoding="utf-8") as f:
                f.write(
                    "\n".join(
                        [
                            f"Package: {app.bundle_name}",
                            f"Version: {app.version}",
                            f"Architecture: {self.command.deb_abi(app)}",
                            f"Maintainer: {app.author} <{app.author_email}>",
                            f"Homepage: {app.url}",
                            f"Description: {app.description}",
                            f" {debian_multiline_description(app.long_description)}",
                            f"Depends: {system_runtime_requires}",
                            f"Section: {getattr(app, 'system_section', 'utils')}",
                            "Priority: optional\n",
                        ]
                    )
                )

        with self.command.console.wait_bar("Building Debian package..."):
            try:
                # Build the dpkg.
                self.command.tools[app].app_context.run(
                    [
                        "dpkg-deb",
                        "--build",
                        "--root-owner-group",
                        self.command.package_path(app),
                    ],
                    check=True,
                    cwd=self.command.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building .deb package for {app.app_name}."
                ) from e

            # Move the deb file to its final location
            self.command.tools.shutil.move(
                self.command.package_path(app).parent
                / f"{self.command.package_path(app).name}.deb",
                self.distribution_path(app),
            )


class LinuxRPMPackagingFormat(LinuxSystemPackagingFormat):
    @property
    def name(self) -> str:
        return "rpm"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info("Building .rpm package...", prefix=app.app_name)

        # The long description *must* exist.
        if app.long_description is None:
            raise BriefcaseCommandError(
                "App configuration does not define `long_description`. "
                "Red Hat projects require a long description."
            )

        # Generate the rpmbuild layout
        rpmbuild_path = self.command.bundle_path(app) / "rpmbuild"
        with self.command.console.wait_bar("Generating rpmbuild layout..."):
            if rpmbuild_path.exists():
                self.command.tools.shutil.rmtree(rpmbuild_path)

            (rpmbuild_path / "BUILD").mkdir(parents=True)
            (rpmbuild_path / "BUILDROOT").mkdir(parents=True)
            (rpmbuild_path / "RPMS").mkdir(parents=True)
            (rpmbuild_path / "SOURCES").mkdir(parents=True)
            (rpmbuild_path / "SRPMS").mkdir(parents=True)
            (rpmbuild_path / "SPECS").mkdir(parents=True)

        # Add runtime package dependencies. App config has been finalized,
        # so this will be the target-specific definition, if one exists.
        system_runtime_requires = [
            "python3",
            *getattr(app, "system_runtime_requires", []),
        ]

        # Write the spec file
        with (
            self.command.console.wait_bar("Write RPM spec file..."),
            (rpmbuild_path / "SPECS" / f"{app.app_name}.spec").open(
                "w", encoding="utf-8"
            ) as f,
        ):
            f.write(
                "\n".join(
                    [
                        # By default, rpmbuild thinks all .py files are executable,
                        # and if a .py doesn't have a shebang line, it will
                        # tell you that it will remove the executable bit -
                        # even if the executable bit isn't set.
                        # We disable the processor that does this.
                        "%global __brp_mangle_shebangs %{nil}",
                        # rpmbuild tries to strip binaries, which messes with
                        # binary wheels. Disable these checks.
                        "%global __brp_strip %{nil}",
                        "%global __brp_strip_static_archive %{nil}",
                        "%global __brp_strip_comment_note %{nil}",
                        # Disable RPATH checking, because check-rpaths can't deal with
                        # the structure of manylinux wheels
                        "%global __brp_check_rpaths %{nil}",
                        # Disable all the auto-detection that tries to magically
                        # determine requirements from the binaries
                        (
                            "%global __requires_exclude_from"
                            f" ^%{{_libdir}}/{app.app_name}/.*$"
                        ),
                        (
                            "%global __provides_exclude_from"
                            f" ^%{{_libdir}}/{app.app_name}/.*$"
                        ),
                        # Disable debug processing.
                        "%global _enable_debug_package 0",
                        "%global debug_package %{nil}",
                        "",
                        # Base package metadata
                        f"Name:           {app.app_name}",
                        f"Version:        {app.version}",
                        f"Release:        {getattr(app, 'revision', 1)}%{{?dist}}",
                        f"Summary:        {app.description}",
                        "",
                        # TODO: Add license information (see #1829)
                        "License:        Unknown",
                        f"URL:            {app.url}",
                        "Source0:        %{name}-%{version}.tar.gz",
                        "",
                    ]
                    + [
                        f"Requires:       {requirement}"
                        for requirement in system_runtime_requires
                    ]
                    + [
                        "",
                        f"ExclusiveArch:  {self.command.rpm_abi(app)}",
                        "",
                        "%description",
                        app.long_description,
                        "",
                        "%prep",
                        "%autosetup",
                        "",
                        "%build",
                        "",
                        "%install",
                        "cp -r usr %{buildroot}/usr",
                    ]
                )
            )

            f.write("\n\n%files\n")
            # Build the file manifest. Include any file that is found; also include
            # any directory that includes an app_name component, as those paths
            # will need to be cleaned up afterwards. Files that *aren't*
            # in <app_name> (sub)directories (e.g., /usr/bin/<app_name> or
            # /usr/share/man/man1/<app_name>.1.gz) will be included, but paths
            # *not* cleaned up, as they're part of more general system structures.
            for filename in sorted(self.command.package_path(app).glob("**/*")):
                path = filename.relative_to(self.command.package_path(app))

                if filename.is_dir():
                    if app.app_name in path.parts:
                        f.write(f'%dir "/{path}"\n')
                else:
                    f.write(f'"/{path}"\n')

            # Add the changelog content to the bottom of the spec file.
            f.write("\n%changelog\n")
            changelog = find_changelog_filename(self.command.base_path)

            if changelog is None:
                raise BriefcaseCommandError("""\
Your project does not contain a changelog file with a known file name. You
must provide a changelog file in the same directory as your `pyproject.toml`,
with a known changelog file name (one of 'CHANGELOG', 'HISTORY', 'NEWS' or
'RELEASES'; the file may have an extension of '.md', '.rst', or '.txt', or have
no extension).
""")

            # Write the changelog content
            f.write((self.command.base_path / changelog).read_text(encoding="utf-8"))

        with (
            self.command.console.wait_bar("Building source archive..."),
            tarfile.open(
                rpmbuild_path
                / f"SOURCES/{self.command.bundle_package_path(app).name}.tar.gz",
                "w:gz",
            ) as archive,
        ):
            archive.add(
                self.command.package_path(app),
                arcname=self.command.bundle_package_path(app).name,
            )

        with self.command.console.wait_bar("Building RPM package..."):
            try:
                # Build the rpm.
                self.command.tools[app].app_context.run(
                    [
                        "rpmbuild",
                        "-bb",
                        "--define",
                        f"_topdir {self.command.bundle_path(app) / 'rpmbuild'}",
                        f"./rpmbuild/SPECS/{app.app_name}.spec",
                    ],
                    check=True,
                    cwd=self.command.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building .rpm package for {app.app_name}."
                ) from e

        # Move the rpm file to its final location
        self.command.tools.shutil.move(
            rpmbuild_path
            / "RPMS"
            / self.command.rpm_abi(app)
            / self.command.distribution_filename(app),
            self.distribution_path(app),
        )


class LinuxArchPackagingFormat(LinuxSystemPackagingFormat):
    @property
    def name(self) -> str:
        return "pkg"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info(
            "Building .pkg.tar.zst package...", prefix=app.app_name
        )

        # The description *must* exist.
        # pkgdesc has 80 char limit.
        if app.description is None:
            raise BriefcaseCommandError(
                "App configuration does not define `description`. "
                "Arch projects require a description."
            )

        changelog = find_changelog_filename(self.command.base_path)

        if changelog is None:
            raise BriefcaseCommandError(
                "Your project does not contain a changelog file with a valid file name."
                "\n\n"
                "Create a changelog file with the following as its name (CHANGELOG, "
                "HISTORY, NEWS or RELEASES) with extensions (.md, .rst, .txt or no "
                "extension) in the same directory as your `pyproject.toml` with "
                "details about the release."
            )

        changelog_source = self.command.base_path / changelog

        # Generate the pkgbuild layout
        pkgbuild_path = self.command.bundle_path(app) / "pkgbuild"
        with self.command.console.wait_bar("Generating pkgbuild layout..."):
            if pkgbuild_path.exists():
                self.command.tools.shutil.rmtree(pkgbuild_path)
            pkgbuild_path.mkdir(parents=True)

            # Copy the CHANGELOG file build_path so that it is visible to PKGBUILD
            self.command.tools.shutil.copy(
                changelog_source, pkgbuild_path / "CHANGELOG"
            )

        # Build the source archive
        with (
            self.command.console.wait_bar("Building source archive..."),
            tarfile.open(
                pkgbuild_path / f"{self.command.bundle_package_path(app).name}.tar.gz",
                "w:gz",
            ) as archive,
        ):
            archive.add(
                self.command.package_path(app),
                arcname=self.command.bundle_package_path(app).name,
            )

        # Write the arch PKGBUILD file.
        with self.command.console.wait_bar("Write PKGBUILD file..."):
            # Add runtime package dependencies. App config has been finalized,
            # so this will be the target-specific definition, if one exists.
            system_runtime_requires_list = [
                f"glibc>={app.glibc_version}",
                "python3",
                *getattr(app, "system_runtime_requires", []),
            ]

            system_runtime_requires = " ".join(
                f"'{pkg}'" for pkg in system_runtime_requires_list
            )

            with (pkgbuild_path / "PKGBUILD").open("w", encoding="utf-8") as f:
                f.write(
                    "\n".join(
                        [
                            f"# Maintainer: {app.author} <{app.author_email}>",
                            f'export PACKAGER="{app.author} <{app.author_email}>"',
                            f"pkgname={app.app_name}",
                            f"pkgver={app.version}",
                            f"pkgrel={getattr(app, 'revision', 1)}",
                            f'pkgdesc="{app.description}"',
                            f"arch=('{self.command.pkg_abi(app)}')",
                            f'url="{app.url}"',
                            "license=('Unknown')",
                            f"depends=({system_runtime_requires})",
                            "changelog=CHANGELOG",
                            'source=("$pkgname-$pkgver.tar.gz")',
                            "md5sums=('SKIP')",
                            "options=('!strip')",
                            "package() {",
                            '    cp -r "$srcdir/$pkgname-$pkgver/usr/" "$pkgdir"/usr/',
                            "}",
                        ]
                    )
                )

        with self.command.console.wait_bar("Building Arch package..."):
            try:
                # Build the pkg.
                self.command.tools[app].app_context.run(
                    [
                        "makepkg",
                    ],
                    env={"PKGEXT": ".pkg.tar.zst"},
                    check=True,
                    cwd=pkgbuild_path,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building .pkg.tar.zst package for {app.app_name}."
                ) from e

            # Move the pkg file to its final location
            self.command.tools.shutil.move(
                pkgbuild_path / self.command.distribution_filename(app),
                self.distribution_path(app),
            )
