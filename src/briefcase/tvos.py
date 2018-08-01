import os
import shutil

from .app import app


class tvos(app):
    description = "Create a tvOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(tvos, self).finalize_options()

        # Set platform-specific options
        self.platform = 'tvOS'
        self.support_project = "Python-Apple-support"

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir

    def install_icon(self):
        for size, description in [('400', 'Small'), ('1280', 'Large')]:
            for layer in ['Front', 'Middle', 'Back']:
                icon_file = '{}-{}-{}.png'.format(self.icon, size, layer.lower())
                if not os.path.exists(icon_file):
                    icon_file = '{}-{}.png'.format(self.icon, size)

                if os.path.exists(icon_file):
                    shutil.copyfile(
                        icon_file,
                        os.path.join(
                            self.resource_dir,
                            self.distribution.get_name(),
                            'Assets.xcassets',
                            'App Icon & Top Shelf Image.brandassets',
                            'App Icon - {}.imagestack'.format(description),
                            '{}.imagestacklayer'.format(size),
                            'Content.imageset',
                            '{}.png'.format(description.lower()))
                    )
                else:
                    print("WARNING: No {} {} icon file available".format(description.lower(), layer.lower()))

        shelf_file = '{}-1920.png'.format(self.splash)
        if os.path.exists(shelf_file):
            shutil.copyfile(
                icon_file,
                os.path.join(
                    self.resource_dir,
                    self.distribution.get_name(),
                    'Assets.xcassets',
                    'App Icon & Top Shelf Image.brandassets',
                    'Top Shelf Image.imageset',
                    'shelf.png')
            )
        else:
            print("WARING: No top shelf image available.")

    def install_splash(self):
        splash_file = '{}-1920x1080.png'.format(self.splash)
        if os.path.exists(splash_file):
            shutil.copyfile(
                splash_file,
                os.path.join(self.resource_dir, self.distribution.get_name(), 'Assets.xcassets', 'LaunchImage.launchimage', 'launch.png')
            )
        else:
            print("WARING: No splash file available.")
