import os
import shutil

from .app import app


class ios(app):
    description = "Create an iOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'iOS'
        self.support_project = "pybee/Python-Apple-Support"

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir

    def install_icon(self):
        last_size = None
        for size in ['180', '167', '152', '120', '87', '80', '76', '58', '40', '29']:
            icon_file = '%s-%s.png' % (self.icon, size)
            if os.path.exists(icon_file):
                last_size = size
            else:
                if last_size:
                    print("WARNING: No %sx%s icon file available; using %sx%s" % (size, size, last_size, last_size))
                    icon_file = '%s-%s.png' % (self.icon, last_size)
                else:
                    icon_file = None

            if icon_file:
                shutil.copyfile(
                    icon_file,
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'AppIcon.appiconset', 'icon-%s.png' % size)
                )
            else:
                print("WARNING: No %sx%s icon file available." % (size, size))

    def install_splash(self):
        for size in ['1024x768', '1536x2048', '2048x1536', '768x1024', '640x1136', '640x960']:
            splash_file = '%s-%s.png' % (self.splash, size)

            if os.path.exists(splash_file):
                shutil.copyfile(
                    splash_file,
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'LaunchImage.launchimage', 'launch-%s.png' % size)
                )
            else:
                print("WARNING: No %s splash file available." % size)
