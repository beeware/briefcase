import os
import shutil
import subprocess

try:
    from urllib.request import urlopen
except ImportError:  # Python 2 compatibility
    from urllib2 import urlopen

import pip

from .app import app


class django(app):
    description = "Create a django app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'icon', 'guid', 'description', 'class_name', 'secret_key'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Django'

        if self.dir is None:
            self.dir = "django"

        self.resource_dir = self.dir

        # Django has no support package
        self.skip_support_pkg = True

    @property
    def app_dir(self):
        return os.path.join(os.getcwd(), self.dir)

    def install_icon(self):
        raise RuntimeError("Django doesn't support icons.")

    def install_splash(self):
        raise RuntimeError("Django doesn't support splash screens.")

    def install_support_package(self):
        pass

    def install_platform_requirements(self):
        print(" * Installing plaform requirements...")

        if self.app_requires:
            pip.main([
                    'install',
                    '--upgrade',
                    '--force-reinstall',
                ] + self.app_requires
            )
        else:
            print("No platform requirements.")

    def install_extras(self):
        # Install additional elements required for Django
        print(" * Installing extras...")
        print("   - Installing NPM requirements...")

        npm = shutil.which("npm")
        subprocess.Popen([npm, "install"], cwd=os.path.abspath(self.dir)).wait()

        print("   - Building Webpack assets...")
        subprocess.Popen([npm, "run", "build"], cwd=os.path.abspath(self.dir)).wait()
