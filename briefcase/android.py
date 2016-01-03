import os
import shutil

from .app import app


class android(app):
    description = "Create an Android app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Android'
        self.support_platform = 'Android'

        if self.dir is None:
            self.dir = 'android'

        self.resource_dir = self.dir

    def install_icon(self):
        last_size = None
        for size, suffix in [('192', '-xxxhdpi'), ('144', '-xxhdpi'), ('96', '-xhdpi'), ('96', ''), ('72', '-hdpi'), ('48', '-mdpi'), ('36', '-ldpi')]:
            if isinstance(self.icon, dict):
                try:
                    icon_file = self.icon[size]
                    last_size = size
                except KeyError:
                    icon_file = self.icon.get(last_size, None)
                    if icon_file:
                        print("WARING: No %sx%s icon file available; using %sx%s" % (size, size, last_size, last_size))
            else:
                icon_file = self.icon

            if icon_file:
                shutil.copyfile(
                    icon_file,
                    os.path.join(self.resource_dir, 'res', 'drawable%s' % suffix, 'icon' + os.path.splitext(icon_file)[1])
                )
            else:
                print("WARING: No %sx%s icon file available." % (size, size))
