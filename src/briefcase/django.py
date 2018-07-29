import os
import shutil
import subprocess
import sys
import webbrowser

try:
    from urllib.request import urlopen
except ImportError:  # Python 2 compatibility
    from urllib2 import urlopen

from pip import _internal as pip

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

        # Set the default device to be the loopback, port 8042
        if self.device_name is None:
            self.device_name = 'localhost:8042'

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
            return '{}.0.0'.format(*parts)
        elif len(parts) == 2:
            return '{}.{}.0'.format(*parts)
        else:
            return '{}.{}.{}'.format(*parts[:3])

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
        print(" * Installing NPM requirements...")
        subprocess.Popen(
            [shutil.which("npm"), "install"],
            cwd=os.path.abspath(self.dir)
        ).wait()

    def post_install(self):
        print()
        print("Installation complete.")
        if not self.build:
            print()
            print("Before you run this Django project, you should review the value")
            print("of the settings in django/briefcase/settings/.env to ensure they")
            print("are appropriate for your machine.")
            print()
            print("Once you've confirmed the settings are OK, you should run:")
            print()
            print("    $ cd django")
            print("    $ npm run build")
            print("    $ ./manage.py migrate")
            print("    $ ./manage.py runserver")
            print()
            print("This will apply the initial migration and start a test server.")
            print()
            print("You can then point a web browser at http://127.0.0.1:8000 to")
            print("view your running application.")
            print()

    def build_app(self):
        print(" * Building Webpack assets...")
        proc = subprocess.Popen(
            [shutil.which("npm"), "run", "build"],
            cwd=os.path.abspath(self.dir)
        )
        proc.wait()
        if proc.returncode != 0:
            return False

        print(' * Applying migrations...')
        proc = subprocess.Popen([
                sys.executable, './manage.py', 'migrate'
            ],
            cwd=os.path.abspath(self.dir)
        )
        proc.wait()
        return proc.returncode == 0

    def start_app(self):
        print(" * Starting Django server on {}".format(self.device_name))
        runserver = subprocess.Popen([
                sys.executable, './manage.py', 'runserver',
                '--noreload',
                self.device_name
            ],
            cwd=os.path.abspath(self.dir)
        )
        print(" * Opening browser...")
        webbrowser.open('http://{}'.format(self.device_name))

        # Wait for the runserver to exit.
        runserver.wait()
