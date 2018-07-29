import os
import shutil
import subprocess
import sys

from .app import app


class macos(app):
    description = "Create a macOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'download_dir', 'document_types'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(macos, self).finalize_options()

        # Set platform-specific options
        self.platform = 'macOS'
        self.support_project = "Python-Apple-support"

        if self.dir is None:
            self.dir = 'macOS'

        self.resource_dir = os.path.join(self.dir, '{}.app'.format(self.formal_name), 'Contents', 'Resources')

    def install_icon(self):
        shutil.copyfile(
            "%s.icns" % self.icon,
            os.path.join(self.resource_dir, '%s.icns' % self.distribution.get_name())
        )

        for tag, doctype in self.document_types.items():
            shutil.copyfile(
                "%s.icns" % doctype['icon'],
                os.path.join(self.resource_dir, "%s-%s.icns" % (self.distribution.get_name(), tag))
            )

    def install_splash(self):
        raise RuntimeError("macOS doesn't support splash screens.")

    @property
    def launcher_header(self):
        """
        Override the shebang line for launcher scripts
        """
        # https://stackoverflow.com/a/36160331
        pyexe = '../Resources/python/bin/python{}'.format(3 if sys.version_info.major == 3 else '')
        return '#!/bin/sh\n'\
               '"exec" "`dirname $0`/{}" "$0" "$@"\n'.format(pyexe)

    @property
    def launcher_script_location(self):
        macos_dir = os.path.abspath(os.path.join(self.resource_dir, '..', 'MacOS'))
        return macos_dir

    def build_app(self):
        return True

    def post_build(self):
        pass

    def start_app(self):
        print("Starting %s.app" % (self.formal_name))
        subprocess.Popen([
                'open', '%s.app' % self.formal_name
            ],
            cwd=os.path.abspath(self.dir)
        ).wait()
