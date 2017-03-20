import os
import shutil

from .app import app


class android(app):
    description = "Create an Android app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'bundle', 'icon', 'download_dir', 'version_code'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        # Set platform-specific options
        self.platform = 'Android'
        self.support_project = "pybee/voc"

        if self.dir is None:
            self.dir = 'android'

        self.resource_dir = self.dir

    def install_icon(self):
        last_size = None
        for size, suffix in [('192', '-xxxhdpi'), ('144', '-xxhdpi'), ('96', '-xhdpi'), ('96', ''), ('72', '-hdpi'), ('48', '-mdpi'), ('36', '-ldpi')]:
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
                    os.path.join(self.resource_dir, 'res', 'drawable%s' % suffix, 'icon.png')
                )
            else:
                print("WARNING: No %sx%s icon file available." % (size, size))

    def install_splash(self):
        pass

    def post_run(self):
        print()
        print("Installation complete.")
        print()
        print("Before you compile this Android project, you need to do the following:")
        print()
        print("    * Download the Android SDK Tools")
        print("    * Ensure you have Android API Level 15 downloaded")
        print("    * Ensure the ANDROID_HOME environment variable points at your Android SDK.")
        print("    * Configure your device for debugging")
        print()
        print("To compile, install and run the project on your phone:")
        print()
        print("    $ cd android")
        print("    $ ./gradlew run")
        print()
        print("To view logs while the project runs:")
        print()
        print("    $ adb logcat Python:* *:E")
        print()
