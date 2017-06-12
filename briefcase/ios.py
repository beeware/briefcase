import json
import os
import shutil

import subprocess

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
        self.support_project = "pybee/Python-Apple-Support"

        if self.dir is None:
            self.dir = self.platform

        self.resource_dir = self.dir

        if self.os_version is None:
            self.os_version = 'iOS 10.2'

        if self.device is None:
            self.device = 'iPhone 7 Plus'

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

    def build_app(self):
        project_file = '%s.xcodeproj' % self.formal_name
        build_settings = [
            ('AD_HOC_CODE_SIGNING_ALLOWED', 'YES'),
            ('CODE_SIGN_IDENTITY', '-'),
            ('VALID_ARCHS', '"i386 x86_64"'),
            ('ARCHS', 'x86_64'),
            ('ONLY_ACTIVE_ARCHS', 'NO')
        ]
        build_settings_str = ['%s=%s' % x for x in build_settings]

        print(' * Building XCode project...')

        subprocess.Popen([
            'xcodebuild', ' '.join(build_settings_str), '-project', project_file, '-destination',
            'platform="iOS Simulator,name=%s,OS=%s"' %(self.device, self.os_version), '-quiet', '-configuration',
            'Debug', '-arch', 'x86_64', '-sdk', 'iphonesimulator%s' % (self.os_version.split(' ')[-1],), 'build'
        ], cwd=os.path.abspath(self.dir)).wait()

    def run_app(self):
        working_dir = os.path.abspath(self.dir)

        # Find an appropriate device
        pipe = subprocess.Popen(['xcrun', 'simctl', 'list', '-j'], stdout=subprocess.PIPE)
        pipe.wait()

        data = json.loads(pipe.stdout.read().decode())

        device_list = data['devices'].get(self.os_version, [])
        device_list = [x for x in device_list if x['name'].lower() == self.device.lower()]

        if not device_list:
            print('WARNING: No devices found for OS %s and device name %s'.format(self.os_version, self.device))
            return

        device = device_list[0]

        # Install app and launch simulator
        print(' * Launching app...')

        app_identifier = '.'.join([self.bundle, self.formal_name.replace(' ', '-')])

        subprocess.Popen(['xcrun', 'instruments', '-w', device['udid']]).wait()

        subprocess.Popen(['xcrun', 'simctl', 'uninstall', device['udid'], app_identifier], cwd=working_dir).wait()
        subprocess.Popen([
            'xcrun', 'simctl', 'install', device['udid'],
            os.path.join('build', 'Debug-iphonesimulator', '%s.app' % self.formal_name)
        ], cwd=working_dir).wait()

        subprocess.Popen([
            'xcrun', 'simctl', 'launch', device['udid'], app_identifier
        ]).wait()