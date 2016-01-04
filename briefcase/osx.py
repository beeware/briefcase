import os
import shutil

from .app import app


class osx(app):
    description = "Create an OS/X app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'OSX'
        self.support_project = "pybee/Python-iOS-Support"

        if self.dir is None:
            self.dir = '.'
            self.resource_dir = os.path.join('%s.app' % self.formal_name, 'Contents', 'Resources')
        else:
            self.resource_dir = os.path.join(self.dir, '%s.app' % self.formal_name, 'Contents', 'Resources')

        if isinstance(self.icon, dict):
            iconfile = self.icon['icns']
        else:
            iconfile = self.icon
        self.icon_filename = os.path.join(self.resource_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def install_icon(self):
        shutil.copyfile(self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("OSX doesn't support splash screens.")
