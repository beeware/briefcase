from __future__ import print_function

import os
import json
import re
import sys
import uuid
from urllib.error import URLError

try:
    from urllib.request import urlopen
except ImportError:  # Python 2 compatibility
    from urllib2 import urlopen

from datetime import date
from distutils.core import Command

import pip

from cookiecutter.main import cookiecutter


class app(Command):
    description = "Create a native application to wrap this project"

    user_options = [
        ('dir=', 'd',
         "Directory to put the project in"),
        ('formal-name=', None,
         "Formal name for the project"),
        ('class-name=', None,
         "Name of the class representing the app."),
        ('organization-name=', None,
         "Name of the organization managing the project"),
        ('template=', None,
         "Template (or template repository URL) to use."),
        ('bundle', None,
         'Bundle identifier for the author organization - usually a reversed domain (e.g., "org.python")'),
        ('icon=', None,
         "Name of the icon file."),
        ('guid=', None,
         "GUID identifying the app."),
        ('splash=', None,
         "Name of the splash screen file."),
        ('app-requires', None,
         'List of platform-specific requirements for this app.'),
        ('support-pkg=', 's',
         'URL for the support package to use'),
        ('download-dir=', None,
         "Directory where the project support packages will be cached"),
    ]

    def initialize_options(self):
        self.dir = None
        self.formal_name = None
        self.class_name = None
        self.organization_name = None
        self.template = None
        self.bundle = None
        self.icon = None
        self.splash = None
        self.app_requires = None
        self.support_pkg = None
        self.download_dir = None
        self.version_code = None
        self.guid = None

    def finalize_options(self):
        if self.formal_name is None:
            self.formal_name = self.distribution.get_name().title()

        # The default classname for the app is a simplified version
        # of the formal name: "My Super-App" -> "MySuperApp"
        if self.class_name is None:
            self.class_name = re.sub('[^a-zA-Z]', '', self.formal_name.title())

        if self.organization_name is None:
            self.organization_name = self.distribution.get_author().title()

        if self.bundle is None:
            if self.distribution.get_author_email():
                domain = self.distribution.get_author_email().split('@')[-1]
            else:
                domain = 'org.python'
            self.bundle = '.'.join(reversed(domain.split('.')))

        if self.download_dir is None:
            self.download_dir = os.path.expanduser(os.path.join('~', '.briefcase'))

        # The Version Code is a pure-string, numerically sortable
        # version number.
        match = re.match('(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<revision>\d+))?)?', self.distribution.get_version())
        self.version_code = '%02d%02d%02d' % (
            int(match.groups()[0]) if match.groups()[0] else 0,
            int(match.groups()[2]) if match.groups()[2] else 0,
            int(match.groups()[4]) if match.groups()[4] else 0,
        )

        # The app's GUID (if not manually specified) is a namespace UUID
        # based on the URL for the app.
        if self.guid is None:
            self.guid = uuid.uuid3(uuid.NAMESPACE_URL, self.distribution.get_url())

        pip.utils.ensure_dir(self.download_dir)

    def find_support_pkg(self):
        api_url = 'https://api.github.com/repos/%s/releases' % self.support_project

        try:
            releases = json.loads(urlopen(api_url).read().decode('utf8'))
        except URLError:
            print()
            print("We had trouble connecting to Github to look for appropriate")
            print("support packages. This can happen when you have tried too many")
            print("times. If you are working on briefcase, please use the specified")
            print("--support-pkg flag for development.")
            return None

        candidates = []
        for release in releases:
            if release['tag_name'].startswith("%s.%s-" % (sys.version_info.major, sys.version_info.minor)):
                for asset in release['assets']:
                    if asset['name'].endswith('.tar.gz') and self.platform in asset['name']:
                        candidates.append((release['created_at'], asset['browser_download_url']))

        try:
            return sorted(candidates, reverse=True)[0][1]
        except IndexError:
            return None

    def generate_app_template(self):
        print(" * Writing application template...")

        if self.template is None:
            self.template = 'https://github.com/pybee/Python-%s-template.git' % self.platform
        print("Project template: %s" % self.template)

        cookiecutter(
            self.template,
            no_input=True,
            checkout='%s.%s' % (sys.version_info.major, sys.version_info.minor),
            extra_context={
                'app_name': self.distribution.get_name(),
                'formal_name': self.formal_name,
                'organization_name': self.organization_name,
                'dir_name': self.dir,
                'bundle': self.bundle,
                'year': date.today().strftime('%Y'),
                'month': date.today().strftime('%B'),
                'version': self.distribution.get_version(),
                'class_name': self.class_name,
                'version_code': self.version_code,
                'guid': self.guid,
            }
        )

    def install_app_requirements(self):
        print(" * Installing requirements...")
        if self.distribution.install_requires:
            pip.main([
                    'install',
                    '--upgrade',
                    '--force-reinstall',
                    '--target=%s' % os.path.join(os.getcwd(), self.resource_dir, 'app_packages')
                ] + self.distribution.install_requires
            )
        else:
            print("No requirements.")

    def install_platform_requirements(self):
        print(" * Installing plaform requirements...")
        if self.app_requires:
            pip.main([
                    'install',
                    '--upgrade',
                    '--force-reinstall',
                    '--target=%s' % os.path.join(os.getcwd(), self.resource_dir, 'app_packages')
                ] + self.app_requires
            )
        else:
            print("No platform requirements.")

    def install_code(self):
        print(" * Installing project code...")
        pip.main([
                'install',
                '--upgrade',
                '--force-reinstall',
                '--no-dependencies',  # We just want the code, not the dependencies
                '--target=%s' % os.path.join(os.getcwd(), self.resource_dir, 'app'),
                '.'
            ])

    def install_resources(self):
        if self.icon:
            print(" * Adding icons...")
            self.install_icon()
        else:
            print(" * No icons defined - using default...")

        if self.splash:
            print(" * Adding splash screens...")
            self.install_splash()
        else:
            print(" * No splash screen defined...")

    def install_support_package(self):
        if self.support_pkg is None:
            print(" * Determining best support package...")
            self.support_pkg = self.find_support_pkg()

        if self.support_pkg:
            print(" * Installing support package...")
            print("Support package: ", self.support_pkg)
            pip.download.unpack_url(
                pip.index.Link(self.support_pkg),
                os.path.join(os.getcwd(), self.resource_dir),
                download_dir=self.download_dir,
            )
        else:
            print()
            print("No pre-built support package could be found for Python %s.%s." % (sys.version_info.major, sys.version_info.minor))
            print("You will need to compile your own. You may want to start with")
            print("the code from https://github.com/%s and" % self.support_project)
            print("then specify the compiled tarball with:")
            print()
            print("    python setup.py %s --support-pkg=<path to tarball>" % self.platform.lower())
            print()

    def post_run(self):
        print()
        print("Installation complete.")

    def run(self):
        self.generate_app_template()
        self.install_app_requirements()
        self.install_platform_requirements()
        self.install_code()
        self.install_resources()
        self.install_support_package()

        self.post_run()
