from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict


class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: list[str]
    host_folders: list[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class DebuggerConfig(TypedDict):
    host: str
    port: int
    app_path_mappings: AppPathMappings | None
    app_packages_path_mappings: AppPackagesPathMappings | None


class DebuggerConnectionMode(str, enum.Enum):
    SERVER = "server"
    CLIENT = "client"


class BaseDebugger(ABC):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    @abstractmethod
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        raise NotImplementedError

    @abstractmethod
    def create_debugger_support_pkg(self, dir: Path) -> None:
        """Create the support package for the debugger.
        This package will be installed inside the packaged app bundle.

        :param dir: Directory where the support package should be created.
        """

    def _create_debugger_support_pkg_base(
        self, dir: Path, dependencies: list[str]
    ) -> None:
        """Create the base for the support package for the debugger.

        :param dir: Directory where the support package should be created.
        :param dependencies: List of dependencies to include in the package.
        """
        pyproject = dir / "pyproject.toml"
        setup = dir / "setup.py"

        pyproject.write_text(
            f"""\
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "briefcase-debugger-support"
version = "0.1.0"
description = "Add-on for briefcase to add remote debugging."
license = {{ file = "MIT" }}
dependencies = {dependencies}
""",
            encoding="utf-8",
        )

        setup.write_text(
            '''\
import os
import setuptools
from setuptools.command.install import install

# Copied from setuptools:
# (https://github.com/pypa/setuptools/blob/7c859e017368360ba66c8cc591279d8964c031bc/setup.py#L40C6-L82)
class install_with_pth(install):
    """
    Custom install command to install a .pth file for distutils patching.

    This hack is necessary because there's no standard way to install behavior
    on startup (and it's debatable if there should be one). This hack (ab)uses
    the `extra_path` behavior in Setuptools to install a `.pth` file with
    implicit behavior on startup to give higher precedence to the local version
    of `distutils` over the version from the standard library.

    Please do not replicate this behavior.
    """

    _pth_name = 'briefcase_debugger_support'
    _pth_contents = "import briefcase_debugger_support"

    def initialize_options(self):
        install.initialize_options(self)
        self.extra_path = self._pth_name, self._pth_contents

    def finalize_options(self):
        install.finalize_options(self)
        self._restore_install_lib()

    def _restore_install_lib(self):
        """
        Undo secondary effect of `extra_path` adding to `install_lib`
        """
        suffix = os.path.relpath(self.install_lib, self.install_libbase)

        if suffix.strip() == self._pth_contents.strip():
            self.install_lib = self.install_libbase

setuptools.setup(
    cmdclass={'install': install_with_pth},
)
''',
            encoding="utf-8",
        )
