import errno
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import uuid
from datetime import date
from distutils.core import Command

import boto3
import pkg_resources
import requests
from botocore.handlers import disable_signing
from cookiecutter.main import cookiecutter
from setuptools.command import easy_install


def download_url(url, download_dir):
    filename = os.path.join(download_dir, os.path.basename(url))

    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            response = requests.get(url, stream=True)
            total = response.headers.get('content-length')

            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                for data in response.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                    downloaded += len(data)
                    f.write(data)
                    done = int(50 * downloaded / total)
                    print('\r{}{} {}%'.format('█' * done, '.' * (50-done), 2*done), end='', flush=True)
        print()
    else:
        print('Already downloaded')
    return filename


class app(Command):
    description = "Create a native application to wrap this project"

    user_options = [
        ('dir=', 'd',
         "Directory to put the project in"),
        ('formal-name=', None,
         "Formal name for the project"),
        ('class-name=', None,
         "Entry class name for the project"),
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
        ('secret-key=', None,
         "Secret key for the app."),
        ('splash=', None,
         "Name of the splash screen file."),
        ('app-requires', None,
         'List of platform-specific requirements for this app.'),
        ('support-pkg=', None,
         'URL for the support package to use'),
        ('download-dir=', None,
         "Directory where the project support packages will be cached"),
        ('build', 'b',
         "Build the project after generating"),
        ('start', 's',
         "Start the application after building"),
        ('os-version=', None,
         "Set the device OS version. (e.g., iOS 10.2)"),
        ('device-name=', None,
         "Set the device to run. (e.g., iPhone 7 Plus)"),
        ('sanitize-version', None,
         "Forces installer version to only contain numbers."),
        ('clean', None,
         "Delete any artifacts from previous run")
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
        self.support_dir = None
        self.download_dir = None
        self.document_types = None
        self.version_code = None
        self.guid = None
        self.secret_key = None
        self.build = False
        self.start = False
        self.os_version = None
        self.device_name = None
        self.sanitize_version = None
        self.clean = None

    def finalize_options(self):
        if self.formal_name is None:
            self.formal_name = self.distribution.get_name().title()

        if self.class_name is None:
            CLASS_NAME_CHARS = re.compile('[^a-zA-Z]')
            self.class_name = CLASS_NAME_CHARS.sub('', self.formal_name.title())

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

        if self.document_types is None:
            self.document_types = {}

        # The Version Code is a pure-string, numerically sortable
        # version number.
        match = re.match('(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<revision>\d+))?)?', self.distribution.get_version())
        self._numeric_version_parts = (
            int(match.groups()[0]) if match.groups()[0] else 0,
            int(match.groups()[2]) if match.groups()[2] else 0,
            int(match.groups()[4]) if match.groups()[4] else 0,
        )
        self.version_code = '%02d%02d%02d' % self._numeric_version_parts
        self.version_numeric = '%d.%d.%d' % self._numeric_version_parts

        # The app's GUID (if not manually specified) is a namespace UUID
        # based on the URL for the app.
        if self.guid is None:
            self.guid = uuid.uuid3(uuid.NAMESPACE_URL, self.distribution.get_url())

        # The secret key is 40 characters of entropy
        if self.secret_key is None:
            self.secret_key = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for i in range(40))

        # Ensure the download directory exists
        try:
            os.makedirs(self.download_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        if self.start:
            self.build = True

    def find_support_pkg(self):
        # Get an S3 client, and disable signing (so we don't need credentials)
        S3_BUCKET = 'pybee-briefcase-support'
        S3_REGION = 'us-west-2'
        S3_URL = 'https://{}.s3-{}.amazonaws.com/'.format(S3_BUCKET, S3_REGION)

        s3 = boto3.client('s3', region_name=S3_REGION)
        s3.meta.events.register('choose-signer.s3.*', disable_signing)

        top_build_number = 0
        top_build = None
        paginator = s3.get_paginator('list_objects')
        for page in paginator.paginate(
                        Bucket=S3_BUCKET,
                        Prefix='{}/{}.{}/{}/'.format(
                            self.support_project,
                            sys.version_info.major,
                            sys.version_info.minor,
                            self.platform
                        )):
            for item in page.get('Contents', []):
                build_number = int(
                    item['Key'].rstrip('.tar.gz').split('.')[-1].lstrip('b'))
                if build_number > top_build_number:
                    top_build_number = build_number
                    top_build = item['Key']
        if top_build:
            return S3_URL + top_build
        else:
            return None

    @property
    def app_dir(self):
        return os.path.join(os.getcwd(), self.resource_dir, 'app')

    @property
    def app_packages_dir(self):
        return os.path.join(os.getcwd(), self.resource_dir, 'app_packages')

    @property
    def version(self):
        return self.distribution.get_version()

    @property
    def _python_version(self):
        return '{}.{}'.format(sys.version_info.major, sys.version_info.minor)

    def generate_app_template(self, extra_context=None):
        print(" * Writing application template...")

        if self.sanitize_version and self.version_numeric != self.version:
            print(" ! Version currently contains characters: {}".format(self.version))
            print(" ! Installer version sanitized to: {}".format(self.version_numeric))

            extra_context = extra_context or {}
            extra_context['version'] = self.version_numeric

        if self.template is None:
            template_path = os.path.expanduser('~/.cookiecutters/Python-{}-template'.format(self.platform))
            if os.path.exists(template_path):
                self.template = template_path
                self._git_fetch(template_path)
                self._git_checkout(template_path)
                if not self._has_cookiecutter_json(template_path):
                    print("Directory {} isn't a valid template (no cookiecutter.json found).".format(template_path))
                    sys.exit(1)
                self._git_pull(template_path)
            else:
                self.template = 'https://github.com/pybee/Python-{}-template.git'.format(self.platform)
        print("Project template: {}".format(self.template))
        _extra_context = {
            'app_name': self.distribution.get_name(),
            'formal_name': self.formal_name,
            'class_name': self.class_name,
            'organization_name': self.organization_name,
            'author': self.distribution.get_author(),
            'description': self.distribution.get_description(),
            'dir_name': self.dir,
            'bundle': self.bundle,
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
            'version': self.version,
            'version_code': self.version_code,
            'guid': self.guid,
            'secret_key': self.secret_key,
            'document_types': self.document_types,
        }
        if extra_context:
            _extra_context.update(extra_context)

        cookiecutter(
            self.template,
            no_input=True,
            checkout= self._python_version,
            extra_context=_extra_context
        )

    def _has_cookiecutter_json(self, template_path):
        cookiecutter_json_path = os.path.join(template_path, 'cookiecutter.json')
        return os.path.exists(cookiecutter_json_path)

    def _get_all_branches(self, path):
        branches = subprocess.check_output(["git", "ls-remote", "--heads"], stderr=subprocess.STDOUT, cwd=path)
        branches = branches.decode('utf-8').splitlines()
        branches = branches[1:]
        all_branches = [name.rsplit("/",1)[1] for name in branches]
        return all_branches

    def _git_fetch(self, path):
        subprocess.Popen(["git", "fetch"], cwd=path).wait()

    def _git_checkout(self, path):
        try:
            subprocess.check_output(["git", "checkout", self._python_version], stderr=subprocess.STDOUT, cwd=path)
        except subprocess.CalledProcessError as pull_error:
            error_message = pull_error.output.decode('utf-8')
            print("There is no branch for Python version %r (existing branches: " % self._python_version, ", ".join(self._get_all_branches(path)) + ").")

    def _git_pull(self, path):
        template_name = path.split('/')[-1]
        try:
            subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT, cwd=path)
            print('Template {} succesfully updated.'.format(template_name))
        except subprocess.CalledProcessError as pull_error:
            error_message = pull_error.output.decode('utf-8')
            if 'resolve host' in error_message:
                print('Unable to update template {}, using unpulled.'.format(template_name))
            print(error_message)

    def install_app_requirements(self):
        print(" * Installing requirements...")
        if self.distribution.install_requires:
            subprocess.Popen(
                [
                    "pip", "install",
                    "--upgrade",
                    "--force-reinstall",
                    '--target={}'.format(self.app_packages_dir)
                ] + self.distribution.install_requires,
            ).wait()
        else:
            print("No requirements.")

    def install_platform_requirements(self):
        print(" * Installing platform requirements...")
        if self.app_requires:
            subprocess.Popen(
                [
                    "pip", "install",
                    "--upgrade",
                    "--force-reinstall",
                    '--target={}'.format(self.app_packages_dir)
                ] + self.app_requires,
            ).wait()
        else:
            print("No platform requirements.")

    def install_code(self):
        print(" * Installing project code...")
        subprocess.Popen(
            [
                "pip", "install",
                "--upgrade",
                "--force-reinstall",
                "--no-dependencies",
                '--target={}'.format(self.app_dir),
                '.'
            ],
        ).wait()

    @property
    def launcher_header(self):
        """
        Optionally override the shebang line for launcher scripts
        This should return a suitable relative path which will find the
        bundled python for the relevant platform if the setuptools default
        is not suitable.
        """
        return None

    @property
    def launcher_script_location(self):
        return self.app_dir

    def install_launch_scripts(self):
        exe_names = []
        if self.distribution.entry_points:
            print(" * Creating launchers...")
            subprocess.Popen(
                [
                    "pip", "install",
                    "--upgrade",
                    "--force-reinstall",
                    '--target={}'.format(self.app_dir),
                    'setuptools'
                ],
            ).wait()

            rel_sesources = os.path.relpath(self.resource_dir, self.launcher_script_location)
            rel_sesources_split = ', '.join(["'%s'" % f for f in rel_sesources.split(os.sep)])

            easy_install.ScriptWriter.template = textwrap.dedent("""
                # EASY-INSTALL-ENTRY-SCRIPT: %(spec)r,%(group)r,%(name)r
                __requires__ = %(spec)r
                import os
                import re
                import sys
                import site
                from os.path import dirname, abspath, join
                resources = abspath(join(dirname(__file__), {}))
                site.addsitedir(join(resources, 'app'))
                site.addsitedir(join(resources, 'app_packages'))
                os.environ['PATH'] += os.pathsep + resources

                from pkg_resources import load_entry_point

                if __name__ == '__main__':
                    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
                    sys.exit(
                        load_entry_point(%(spec)r, %(group)r, %(name)r)()
                    )
            """.format(rel_sesources_split)).lstrip()

            ei = easy_install.easy_install(self.distribution)
            for dist in pkg_resources.find_distributions(self.app_dir):
                # Note: this is a different Distribution class to self.distribution
                ei.args = True  # Needs something to run finalize_options
                ei.finalize_options()
                ei.script_dir = self.launcher_script_location
                for args in easy_install.ScriptWriter.best().get_args(dist, header=self.launcher_header):
                    ei.write_script(*args)

                # Grab names of launchers
                for entry_points in dist.get_entry_map().values():
                    exe_names.extend(entry_points.keys())

            if self.formal_name not in exe_names:
                print(" ! No entry_point matching formal_name, \n"
                      "   template builtin script will be main launcher.")

        return exe_names

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

        if self.support_dir is None:
            self.support_dir = self.resource_dir

        if self.support_pkg:
            print(" * Installing support package...")
            print("Support package:", self.support_pkg)

            # Download and unpack the support package.
            filename = download_url(url=self.support_pkg, download_dir=self.download_dir)

            destination = os.path.join(os.getcwd(), self.support_dir)
            shutil.unpack_archive(filename, extract_dir=destination)
        else:
            print()
            print("No pre-built support package could be found for Python %s.%s." % (sys.version_info.major, sys.version_info.minor))
            print("You will need to compile your own. You may want to start with")
            print("the code from https://github.com/pybee/%s and" % self.support_project)
            print("then specify the compiled tarball with:")
            print()
            print("    python setup.py {} --support-pkg=<path to tarball>".format(self.platform.lower()))
            print()
            sys.exit(1)

    def install_extras(self):
        pass

    def build_app(self):
        pass

    def run_app(self):
        pass

    def post_install(self):
        print()
        print("Installation complete.")

    def post_build(self):
        print()
        print("Build complete.")

    def start_app(self):
        print("Don't know how to start {} applications.".format(self.platform))

    def post_start(self):
        print()
        print("App started.")

    def run(self):
        full_generation = True
        if os.path.exists(self.dir):
            print()
            if self.clean:
                print(" * Deleting existing content...")
                if os.path.isdir(self.dir):
                    shutil.rmtree(self.dir)
                else:
                    os.remove(self.dir)
            else:
                print(" * Updating user code...")
                full_generation = False
        if full_generation:
            self.generate_app_template()
            self.install_support_package()
        self.install_app_requirements()
        self.install_platform_requirements()
        self.install_code()
        self.install_launch_scripts()
        self.install_resources()
        self.install_extras()
        self.post_install()
        if self.build:
            success = self.build_app()
            if success is None or success is True:
                self.post_build()
        if self.start:
            self.start_app()
            self.post_start()
