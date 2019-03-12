import os
import shutil
import subprocess
import sys

import dmgbuild

from .app import app


class macos(app):
    description = "Create a macOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        options = ('formal_name', 'organization_name',
                   'bundle', 'icon', 'download_dir', 'document_types', 'background_image')
        for attr in options:
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(macos, self).finalize_options()

        # Set platform-specific options
        self.platform = 'macOS'
        self.support_project = "Python-Apple-support"

        if self.dir is None:
            self.dir = 'macOS'
        self.app_location = os.path.join(self.dir, '{}.app'.format(
            self.formal_name))  # Location of the .app file

        self.resource_dir = os.path.join(
            self.app_location, 'Contents', 'Resources')

    def install_icon(self):
        shutil.copyfile(
            "%s.icns" % self.icon,
            os.path.join(self.resource_dir, '%s.icns' % self.distribution.get_name())
        )

        for tag, doctype in self.document_types.items():
            shutil.copyfile(
                "%s.icns" % doctype['icon'],
                os.path.join(self.resource_dir, "%s-%s.icns" %
                             (self.distribution.get_name(), tag))
            )

    def install_splash(self):
        raise RuntimeError("macOS doesn't support splash screens.")

    @property
    def launcher_header(self):
        """
        Override the shebang line for launcher scripts
        """
        # https://stackoverflow.com/a/36160331
        pyexe = '../Resources/python/bin/python{}'.format(
            3 if sys.version_info.major == 3 else '')
        return '#!/bin/sh\n'\
               '"exec" "`dirname $0`/{}" "$0" "$@"\n'.format(pyexe)

    @property
    def launcher_script_location(self):
        macos_dir = os.path.abspath(
            os.path.join(self.resource_dir, '..', 'MacOS'))
        return macos_dir

    def build_app(self):
        print("Building DMG file...")
        dmg_name = self.formal_name + '.dmg'
        dmg_path = os.path.join(os.path.abspath(self.dir), dmg_name)

        dmgbuild.build_dmg(
            filename=dmg_path,
            volume_name=self.formal_name,
            settings={
                'files': [self.app_location],
                'symlinks': {'Applications': '/Applications'},
                'background': self.background_image,
                'icon': os.path.join(self.resource_dir, '%s.icns' % self.distribution.get_name()),
            }
        )
        return True

    def post_build(self):
        pass

    def start_app(self):
        print("Starting %s.app" % (self.formal_name))
        subprocess.Popen(
            [
                'open', '%s.app' % self.formal_name
            ],
            cwd=os.path.abspath(self.dir)
        ).wait()
