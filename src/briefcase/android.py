import os
import shutil
import subprocess
import sys

from .app import app


class android(app):
    description = "Create an Android app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'class_name', 'bundle', 'icon', 'splash', 'download_dir', 'version_code'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(android, self).finalize_options()

        # Set platform-specific options
        self.platform = 'Android'
        self.support_project = "Python-Android-support"

        if self.dir is None:
            self.dir = 'android'

        self.resource_dir = self.dir

    def install_icon(self):
        last_size = None
        for size, suffix in [
                    ('192', '-xxxhdpi'),
                    ('144', '-xxhdpi'),
                    ('96', '-xhdpi'),
                    ('72', '-hdpi'),
                    ('48', '-mdpi'),
                    ('36', '-ldpi')
                ]:
            icon_file = '{}-{}.png'.format(self.icon, size)
            if os.path.exists(icon_file):
                last_size = size
            else:
                if last_size:
                    print("WARNING: No {}x{} icon file available; using {}x{}".format(size, size, last_size, last_size))
                    icon_file = '{}-{}.png'.format(self.icon, last_size)
                else:
                    icon_file = None

            if icon_file:
                shutil.copyfile(
                    icon_file,
                    os.path.join(self.resource_dir, 'res', 'drawable{}'.format(suffix), 'icon.png')
                )
            else:
                print("WARNING: No {}x{} icon file available.".format(size, size))

    def install_splash(self):
        last_size = None
        for size, suffix in [
                    ('1280×1920', '-xxxhdpi'),
                    ('960×1440', '-xxhdpi'),
                    ('640×960', '-xhdpi'),
                    ('480x720', '-hdpi'),
                    ('320×480', '-mdpi'),
                    ('240×320', '-ldpi')
                ]:
            splash_file = '{}-{}.png'.format(self.splash, size)
            if os.path.exists(splash_file):
                last_size = size
            else:
                if last_size:
                    print("WARNING: No {} splash file available; using {}".format(size, last_size))
                    splash_file = '{}-{}.png'.format(self.splash, last_size)
                else:
                    splash_file = None

            if splash_file:
                shutil.copyfile(
                    splash_file,
                    os.path.join(self.resource_dir, 'res', 'drawable{}'.format(suffix), 'splash.png')
                )
            else:
                print("WARNING: No {} splash file available.".format(size))

    def post_install(self):
        print()
        print("Installation complete.")
        print()
        if not self.build:
            print("Before you compile this Android project, you need to do the following:")
            print()
            print("    * Download the Android SDK Tools")
            print("    * Ensure you have Android API Level 15 downloaded")
            print("    * Ensure the ANDROID_HOME environment variable points at your Android SDK.")
            print("    * Configure your device or the android simulator for debugging")
            print()
            print("To compile, install and run the project on your phone/simulator:")
            print()
            print("    $ python setup.py android --build --start")
            print()
            print("To view logs while the project runs:")
            print()
            print("    $ adb logcat Python:* *:E")
            print()

    def build_app(self):
        if not self.start:
            print(" * Building {}...".format(self.formal_name))
            if sys.platform == 'win32':
                proc = subprocess.Popen([
                    'cmd.exe', '/c', 'gradlew.bat', 'build'
                ],
                    cwd=os.path.abspath(self.dir)
                )
            else:
                proc = subprocess.Popen([
                        '/usr/bin/env', 'sh', './gradlew', 'build'
                    ],
                    cwd=os.path.abspath(self.dir)
                )
            proc.wait()
            return proc.returncode == 0

    def post_build(self):
        if not self.start:
            super().post_build()

    def start_app(self):
        print("Starting {}".format(self.formal_name))
        if sys.platform == 'win32':
            params = ['cmd.exe', '/c', 'gradlew.bat', 'run']
        else:
            params = ['./gradlew', 'run']
        subprocess.Popen(
            params,
            cwd=os.path.abspath(self.dir)
        ).wait()

        print("    $ adb logcat Python:* *:E")
