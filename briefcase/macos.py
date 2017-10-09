import os
import sys
import shutil
import subprocess

from .app import app


class macos(app):
    description = "Create a macOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(macos, self).finalize_options()

        # Set platform-specific options
        self.platform = 'macOS'
        self.support_project = "Python-Apple-support"

        if self.dir is None:
            self.dir = 'macOS'

        self.resource_dir = os.path.join(self.dir, '%s.app' % self.formal_name, 'Contents', 'Resources')

        iconfile = '%s.icns' % self.icon
        self.icon_filename = os.path.join(self.resource_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def install_icon(self):
        shutil.copyfile("%s.icns" % self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("macOS doesn't support splash screens.")

    @property
    def launcher_header(self):
        """
        Override the shebang line for launcher scripts
        """
        # https://stackoverflow.com/a/36160331
        pyexe = '../Resources/python/bin/python%s' % (3 if sys.version_info.major == 3 else '')
        return '#!/bin/sh\n'\
               '"exec" "`dirname $0`/%s" "$0" "$@"\n' % pyexe

    @property
    def launcher_script_location(self):
        macos_dir = os.path.abspath(os.path.join(self.resource_dir, '..', 'MacOS'))
        return macos_dir

    # def install_launch_scripts(self):
    #     exes = super(macos, self).install_launch_scripts()
        # if self.formal_name in exes:
        #     # If a main launcher has been created, remove template app and symlink to launcher
        #     main_app = os.path.join(self.resource_dir, '..', 'MacOS', self.formal_name)
        #     if os.path.exists(main_app):
        #         os.unlink(main_app)
        #         os.symlink(os.path.join('..', 'Resources', self.formal_name), main_app)

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
