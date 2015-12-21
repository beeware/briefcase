import os
import shutil

from .app import app


class ios(app):
    description = "Create an iOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'iOS'
        self.support_project = 'iOS'

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir

        if not isinstance(self.icon, dict):
            raise RuntimeError('Splash image specifier must be a dictionary')

    def install_icon(self):
        last_size = None
        for size in ['180', '167', '152', '120', '80', '87', '76', '58', '40', '29']:
            if isinstance(self.icon, dict):
                try:
                    icon_file = self.icon[size]
                    last_size = size
                except KeyError:
                    icon_file = self.icon.get(last_size, None)
                    if icon_file:
                        print("WARING: No %sx%s icon file available; using %sx%s" % (size, size, last_size))
            else:
                icon_file = self.icon

            if icon_file:
                shutil.copyfile(
                    icon_file,
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'AppIcon.appiconset', 'icon-%s' % size + os.path.splitext(icon_file)[1])
                )
            else:
                print("WARING: No %s icon file available." % size)

    def install_splash(self):
        for size in ['1024x768', '1536x2048', '2048x1536', '768x1024', '640x1136', '640x960']:
            try:
                icon_file = self.splash[size]
                shutil.copyfile(
                    self.splash[size],
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'LaunchImage.launchimage', 'launch-%s' % size + os.path.splitext(icon_file)[1])
                )
            except KeyError:
                print("WARING: No %s splash file available." % size)
