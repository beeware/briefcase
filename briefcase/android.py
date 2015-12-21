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
            self.dir = self.platform

        self.resource_dir = self.dir
        self.icon_filename = os.path.join(self.resource_dir, self.distribution.get_name() + os.path.splitext(self.icon)[1])

    def install_icon(self):
        last_size = None
        for size in ['180x180', '152x152', '120x120', '80x80', '76x76', '58x58', '40x40', '29x29']:
            if isinstance(self.icon, dict):
                try:
                    icon_file = self.icon[size]
                    last_size = size
                except KeyError:
                    print("WARING: No %sx%s icon file available; using ." % size)
                    icon_file = self.icon.get(last_size, None)
            else:
                icon_file = self.icon

            if icon_file:
                shutil.copyfile(
                    self.icon[size],
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'AppIcon.appiconset', 'icon-%s' % size + os.path.splitext(icon_file)[1])
                )
            else:
                print("WARING: No %sx%s icon file available." % size)

    def install_splash(self):
        for size in ['1024x768', '1536x2048', '2048x1536', '768x1024', '640x1136', '640x960']:
            try:
                icon_file = self.icon[size]
                shutil.copyfile(
                    self.icon[size],
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'LaunchImage.launchimage', 'launch-%s' % size + os.path.splitext(icon_file)[1])
                )
            except KeyError:
                print("WARING: No %sx%s splash file available.")
