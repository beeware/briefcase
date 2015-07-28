import os

from .app import app


class osx(app):
    description = "Create an OS/X app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'download_dir'):
            setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'OSX'

        if self.dir is None:
            self.dir = '.'
            self.resource_dir = os.path.join('%s.app' % self.formal_name, 'Contents', 'Resources')
        else:
            self.resource_dir = os.path.join(self.dir, '%s.app' % self.formal_name, 'Contents', 'Resources')
