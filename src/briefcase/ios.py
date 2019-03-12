import json
import os
import shutil
import subprocess
import sys

from .app import app


class ios(app):
    description = "Create an iOS app to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(ios, self).finalize_options()

        # Set platform-specific options
        self.platform = 'iOS'
        self.support_project = "Python-Apple-support"

        self.device = None

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir

    def install_icon(self):
        last_size = None
        for size in [
                    '1024',  # App Store Icon
                    '180',  # iPhone @3x Icon
                    '167',  # iPad Pro @2x Icon
                    '152',  # iPad @2x Icon, iPad mini @2x Icon
                    '120',  # iPhone @2x Icon, iPhone @3x Spotlight
                    '87',  # iPhone @3x Setting
                    '80',  # iPhone @2x Spotlight, iPad Pro @2x Spotlight,
                           # iPad @2x Spotlight, iPad mini @2x Spotlight
                    '60',  # iPhone @3x Notification
                    '58',  # iPhone @2x Setting, iPad Pro @2x Setting,
                           # iPad @2x Setting, iPad mini Setting
                    '40',  # iPhone @2x Notification, iPad Pro @2x Notification,
                           # iPad @2x Notification, iPad mini @2x Notification

                    # Theoretically deprecated, but still required
                    # by the AppIcon resource file
                    '76',  # iPad @1x Icon
                    '29',  # iPad @1x Notification
                    '20',  # iPhone @1x Notification
                ]:
            icon_file = '%s-%s.png' % (self.icon, size)
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
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'AppIcon.appiconset', 'icon-%s.png' % size)
                )
            else:
                print("WARNING: No {}x{} icon file available.".format(size, size))

    def install_splash(self):
        for size in [
                    '2048×2732',  # 12.9" iPad Pro
                    '2732×2048',  # (landscape)

                    '1668×2224',  # 10.5" iPad Pro
                    '2224×1668',  # (landscape)

                    '1536×2048',  # 9.7" iPad, 7.9" iPad mini 4 (@2x)
                    '2048×1536',  # (landscape)

                    '768×1024',  # 9.7" iPad, 7.9" iPad mini 4 (@1x)
                    '1024×768',  # (landscape)

                    '1242×2688',  # iPhone XS Max
                    '2688×1242',  # (landscape)

                    '828×1792',  # iPhone XR
                    '1792×828',  # (landscape)

                    '1125×2436',  # iPhone X, iPhone XS
                    '2436×1125',  # (landscape)

                    '750×1334',  # iPhone 8, iPhone 7, iPhone 6s
                    '1334×750',  # (landscape)

                    '1242×2208',  # iPhone 8 Plus, iPhone 7 Plus, iPhone 6s Plus
                    '2208×1242',  # (landscape)

                    '640×1136',  # iPhone SE
                    '1136×640',  # (landscape)

                    '640x960',  # iPhone 6
                ]:
            splash_file = '{}-{}.png'.format(self.splash, size)

            if os.path.exists(splash_file):
                shutil.copyfile(
                    splash_file,
                    os.path.join(self.resource_dir, self.distribution.get_name(), 'Images.xcassets', 'LaunchImage.launchimage', 'launch-%s.png' % size)
                )
            else:
                print("WARNING: No {} splash file available.".format(size))

    def set_device_target(self):
        if self.os_version is None or self.device_name is None or self.device is None:
            # Find an appropriate device
            pipe = subprocess.Popen(['xcrun', 'simctl', 'list', '-j'], stdout=subprocess.PIPE)
            pipe.wait()

            data = json.loads(pipe.stdout.read().decode())

            if self.os_version is None:
                os_list = [label for label in data['devices'] if label.startswith('iOS')]
                if len(os_list) == 0:
                    print('No iOS device simulators found', file=sys.stderr)
                    sys.exit(1)
                elif len(os_list) == 1:
                    print('Building for {}...'.format(os_list[0]))
                    self.os_version = os_list[0]
                else:
                    print()
                    while self.os_version is None:
                        print('Available iOS versions:')
                        for i, label in enumerate(os_list):
                            print('  [{}] {}'.format(i+1, label))
                        try:
                            index = int(input('Which iOS version do you want to target: '))
                            self.os_version = os_list[int(index) - 1]
                        except:
                            print("Invalid selection.")
                            print

            if self.device_name is None:
                device_list = data['devices'].get(self.os_version, [])
                if len(device_list) == 0:
                    print('No devices found', file=sys.stderr)
                    sys.exit(2)
                elif len(device_list) == 1:
                    print('Device ID is {}...'.format(device_list[0]))
                    self.device = device_list[0]
                    self.device_name = self.device['name']
                else:
                    print()
                    while self.device_name is None:
                        print('Available devices:')
                        for i, device in enumerate(device_list):
                            print('  [{}] {}'.format(i+1, device['name']))
                        index = int(input('Which device do you want to target: '))
                        try:
                            self.device = device_list[int(index) - 1]
                            self.device_name = self.device['name']
                        except:
                            print("Invalid selection.")
                            print

            if self.device is None:
                device_list = data['devices'].get(self.os_version, [])
                self.device = [x for x in device_list if x['name'].lower() == self.device_name.lower()][0]

    def has_required_xcode_version(self):
        pipe = subprocess.Popen(['xcrun', 'xcodebuild', '-version'], stdout=subprocess.PIPE)
        pipe.wait()

        output = pipe.stdout.read().decode()
        version = tuple(
            int(v)
            for v in output.split('\n')[0].split(' ')[1].split('.')[:2]
        )
        if version < (8, 0):
            print('\nAutomated builds require XCode 8.0 or later', file=sys.stderr)
            return False
        else:
            return True

    def build_app(self):
        if not self.has_required_xcode_version():
            return False

        project_file = '{}.xcodeproj'.format(self.formal_name)
        build_settings = [
            ('AD_HOC_CODE_SIGNING_ALLOWED', 'YES'),
            ('CODE_SIGN_IDENTITY', '-'),
            ('VALID_ARCHS', '"i386 x86_64"'),
            ('ARCHS', 'x86_64'),
            ('ONLY_ACTIVE_ARCHS', 'NO')
        ]
        build_settings_str = ['{}={}'.format(*x) for x in build_settings]

        self.set_device_target()

        print(' * Building XCode project for {} {}...'.format(self.device_name, self.os_version))

        proc = subprocess.Popen([
            'xcodebuild', ' '.join(build_settings_str), '-project', project_file, '-destination',
            'platform="iOS Simulator,name={},OS={}"'.format(self.device_name, self.os_version), '-quiet', '-configuration',
            'Debug', '-arch', 'x86_64', '-sdk', 'iphonesimulator%s' % (self.os_version.split(' ')[-1],), 'build'
        ], cwd=os.path.abspath(self.dir))
        proc.wait()
        return proc.returncode == 0

    def start_app(self):
        if not self.has_required_xcode_version():
            return

        working_dir = os.path.abspath(self.dir)

        self.set_device_target()

        # Install app and launch simulator
        app_identifier = '.'.join([self.bundle, self.formal_name.replace(' ', '-')])

        print()
        print("Starting app on {} {}".format(self.device_name, self.os_version))
        print(' * Starting simulator...')
        subprocess.Popen(
            ['instruments', '-w', self.device['udid']],
            stderr=subprocess.PIPE
        ).communicate()

        print(' * Uninstalling old app version...')
        subprocess.Popen(
            ['xcrun', 'simctl', 'uninstall', self.device['udid'], app_identifier],
            cwd=working_dir
        ).wait()

        print(' * Installing new app version...')
        subprocess.Popen([
            'xcrun', 'simctl', 'install', self.device['udid'],
            os.path.join('build', 'Debug-iphonesimulator', '{}.app'.format(self.formal_name))
        ], cwd=working_dir).wait()

        print(' * Launching app...')
        subprocess.Popen([
            'xcrun', 'simctl', 'launch', self.device['udid'], app_identifier
        ]).wait()
