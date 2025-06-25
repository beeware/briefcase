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

    _pth_name = "briefcase_pdb_debugger_support"
    _pth_contents = "import briefcase_pdb_debugger_support"

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
    cmdclass={"install": install_with_pth},
)
