import os
import shutil

from .app import app


class windows(app):
    description = "Create a Windows installer to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'guid', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Windows'
        self.support_project = "pybee/Python-Microsoft-Support"

        if self.dir is None:
            self.dir = '.'
            self.resource_dir = os.path.join('%s' % self.formal_name, 'Tools')
        else:
            self.resource_dir = os.path.join(self.dir, '%s' % self.formal_name, 'Tools')

        if isinstance(self.icon, dict):
            iconfile = self.icon['ico']
        else:
            iconfile = self.icon
        self.icon_filename = os.path.join(self.resource_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def install_icon(self):
        shutil.copyfile('%s.ico' % self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("Windows doesn't support splash screens.")
