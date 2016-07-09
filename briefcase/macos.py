import os
import shutil

from .app import app


class macos(app):
    description = "Create a macOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'macOS'
        self.support_project = "pybee/Python-Apple-Support"

        if self.dir is None:
            self.dir = 'macOS'

        self.resource_dir = os.path.join(self.dir, '%s.app' % self.formal_name, 'Contents', 'Resources')

        iconfile = '%s.icns' % self.icon
        self.icon_filename = os.path.join(self.resource_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def install_icon(self):
        shutil.copyfile("%s.icns" % self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("macOS doesn't support splash screens.")
