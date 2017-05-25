import os
import stat
import shutil
import subprocess, shlex
import sys
import requests
import tempfile

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

        super(django, self).finalize_options()

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

    @property
    def version(self):
        parts = self.distribution.get_version().split('.')

        if len(parts) == 0:
            return '1.0.0'
        elif len(parts) == 1:
            return '%s.0.0' % tuple(parts)
        elif len(parts) == 2:
            return '%s.%s.0' % tuple(parts)
        else:
            return '%s.%s.%s' % tuple(parts[:3])

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
        node_attributes = {
            'darwin': {
                'url':'https://nodejs.org/dist/v6.10.3/node-v6.10.3.pkg',
                'command_prefix': 'open '
            },
            'linux' : '',
            'win32' : {
                'url' :'https://nodejs.org/dist/v6.10.3/node-v6.10.3-x86.msi',
                'command_prefix': 'msiexec /i '
            }
        }
        system_platform = sys.platform
        required_node_version = '6'
        node = shutil.which('node')
        npm  = shutil.which("npm")
        #workaround in case no node version is found
        node_version = 'No version'
        try:
            node_version_unicode = subprocess.check_output([node, '--version'])
            node_version = node_version_unicode.decode('utf-8')
            print('Node version %s detected' % node_version)
        except:
            node_version = ''
        if node and node_version[1] == required_node_version:
            subprocess.Popen(['npm', 'install'], cwd=os.path.abspath(self.dir)).wait()
        else:
            if node_version[1] != required_node_version:
                err_message = ('ERROR: Cannot run with the current version of Node and Npm, please \n'
                               'unnistall the current version and install Node version 6.x\n'
                               'Installation cancelled.'
                )
            else:
                err_message=('Could not finish installation because NodeJs is not installed\n'
                    'Please install NodeJs at:\n %s' % node_attributes[system_platform]['url'])
            raise RuntimeError(err_message)
        print("   - Building Webpack assets...")
        subprocess.Popen([npm, "run", "build"], cwd=os.path.abspath(self.dir)).wait()

    def django_migrate(self):
        #should we migrate for the user??? #justAsking :)
        #subprocess.Popen(['python', 'manage.py', 'migrate'], cwd=os.path.abspath(self.dir))
        pass

    def post_run(self):
        print()
        print("Installation complete.")
        print()
        print("Before you run this Django project, you should review the value")
        print("of the settings in django/briefcase/settings/.env to ensure they")
        print("are appropriate for your machine.")
        print()
        print("Once you've confirmed the settings are OK, you should run:")
        print()
        print("    $ cd django")
        print("    $ ./manage.py migrate")
        print("    $ ./manage.py runserver")
        print()
        print("This will apply the initial migration and start a test server.")
        print()
        print("You can then point a web browser at http://127.0.0.1:8000 to")
        print("view your running application.")
        print()
