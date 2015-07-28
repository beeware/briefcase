from .app import app


class android(app):
    description = "Create an Android app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'download_dir'):
            setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Android'

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir
