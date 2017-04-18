import os
import distutils.command.install_scripts as orig
from pkg_resources import Distribution, PathMetadata
import shutil
import subprocess
import sys

from .app import app


class windows(app):
    description = "Create a Windows installer to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'guid', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Windows'
        self.support_project = "pybee/Python-Microsoft-Support"

        if self.dir is None:
            self.dir = 'windows'

        self.resource_dir = self.dir
        self.support_dir = os.path.join(self.dir, 'python')

        iconfile = '%s.ico' % self.icon
        self.icon_filename = os.path.join(self.app_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def install_icon(self):
        shutil.copyfile('%s.ico' % self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("Windows doesn't support splash screens.")

    def find_support_pkg(self):
        version = "%s.%s.%s" % sys.version_info[:3]
        return 'https://www.python.org/ftp/python/%s/python-%s-embed-amd64.zip' % (version, version)

    def install_extras(self):
        print(" * Creating application link...")
        subprocess.Popen(["powershell", "-File", "make_link.ps1"], cwd=os.path.abspath(self.dir)).wait()
        os.remove(os.path.join(os.path.abspath(self.dir), 'make_link.ps1'))
