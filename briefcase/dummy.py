import os
import distutils.command.install_scripts as orig
from pkg_resources import Distribution, PathMetadata
import shutil
import subprocess
import sys

from .app import app


class dummy(app):
    description = "Dummy create to test"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'guid', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(dummy, self).finalize_options()

        # Set platform-specific options
        self.platform = 'Dummy'

        if self.dir is None:
            self.dir = 'dummy'

        self.resource_dir = self.dir

    def install_icon(self):
        print('install_icon')

    def install_splash(self):
        print('install_splash')

    def install_support_package(self):
        # No support package; we just use the system python
        print('install_support_package')

    def build_app(self):
        print('build_app')
        return True

    def post_build(self):
        print('post_build')

    def start_app(self):
        print("Starting %s" % (self.formal_name))
