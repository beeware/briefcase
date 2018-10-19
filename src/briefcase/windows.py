import os
import re
import shutil
import struct
import subprocess
import sys
import uuid

from .app import app


class windows(app):
    description = "Create a Windows installer to wrap this project"

    def finalize_options(self):
        # Copy over all the options from the base 'app' command
        finalized = self.get_finalized_command('app')
        for attr in ('formal_name', 'organization_name', 'bundle', 'icon', 'guid', 'splash', 'download_dir'):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(finalized, attr))

        super(windows, self).finalize_options()

        # Set platform-specific options
        self.platform = 'Windows'

        if self.dir is None:
            self.dir = 'windows'

        self.resource_dir = os.path.join(self.dir, 'content')
        self.support_dir = os.path.join(self.dir, 'content', 'python')

    def generate_app_template(self, extra_context=None):
        if self.version_numeric != self.version and not self.sanitize_version:
            print(" ! Windows Installer version can only contain numerals, currently: {}".format(self.version))
            print(" ! --sanitize-version can be used to automatically filter this to {}".format(self.version_numeric))
            exit(1)

        super(windows, self).generate_app_template(extra_context=extra_context)

    def install_icon(self):
        shutil.copyfile(
            '%s.ico' % self.icon,
            os.path.join(self.app_dir, '%s.ico' % self.distribution.get_name())
        )

    def install_splash(self):
        raise RuntimeError("Windows doesn't support splash screens.")

    def find_support_pkg(self):
        version = "%s.%s.%s" % sys.version_info[:3]
        arch = "amd64" if (struct.calcsize("P") * 8) == 64 else "win32"
        return 'https://www.python.org/ftp/python/%s/python-%s-embed-%s.zip' % (version, version, arch)

    @property
    def launcher_header(self):
        """
        Override the shebang line for launcher scripts
        This should return a suitable relative path which will find the
        bundled python for the relevant platform
        """
        return "#!.\python\python.exe\n"

    def install_extras(self):
        print(" * Finalizing application installer script...")

        # Find all the files that need to be put in the installer
        app_root = os.path.join(self.dir, 'content')
        content = []
        contentrefs = []
        shortcuts = []
        dir_ids = []

        def walk_dir(path, depth=0):
            files = []
            parts = path[len(app_root) + 1:].split(os.path.sep)
            for name in os.listdir(path):
                full_path = os.path.join(path, name)

                if parts[0]:
                    full_parts = parts + [name]
                else:
                    full_parts = [name]

                if os.path.isdir(full_path):
                    dir_id = '.'.join(re.sub('[^A-Za-z0-9_]', '_', p) for p in full_parts)
                    if len(dir_id) > 68:
                        dir_id = '...' + dir_id[-65:]
                    while dir_id in dir_ids:
                        dir_id = '...' + dir_id[4:]
                    dir_ids.append(dir_id)

                    content.append(
                        '    ' * (depth + 5) + '<Directory Id="DIR_{}" Name="{}">'.format(
                            dir_id, name
                        )
                    )
                    walk_dir(os.path.join(path, name), depth=depth + 1)

                    content.append('    ' * (depth + 5) + '</Directory>')
                else:
                    files.append(name)

            if files:
                guid = uuid.uuid4()

                content.append('    ' * (depth + 5) + '<Component Id="COMP_{}" Guid="{}">'.format(
                    guid.hex, guid)
                )
                for file in files:
                    content.append('    ' * (depth + 6) + '<File Id="FILE_{}" Source="content/{}/{}" />'.format(
                            uuid.uuid4().hex, '/'.join(parts), file
                        )
                    )
                content.append('    ' * (depth + 5) + '</Component>')
                contentrefs.append('            <ComponentRef Id="COMP_{}"/>'.format(guid.hex))


        walk_dir(app_root)

        if self.distribution.entry_points:
            for entries in self.distribution.entry_points.values():
                for entry in entries:
                    exe_name = entry.split('=')[0].strip()
                    description = self.distribution.get_description()
                    shortcutid = uuid.uuid4().hex
                    shortcuts.append("""\
                            <Shortcut
                                Id="AppShortcut_{shortcutid}"
                                Name="{exe_name}"
                                Icon="ProductIcon"
                                Description="{description}"
                                Target="[AppDir]\\app\\{exe_name}.exe"
                                WorkingDirectory="AppDir" />""".format(**locals()))

        # Generate the full briefcase.wxs file
        briefcase_wxs = os.path.join(self.dir, 'briefcase.wxs')
        briefcase_wxs_orig = briefcase_wxs + '.orig'

        if os.path.exists(briefcase_wxs_orig):
            try:
                os.unlink(briefcase_wxs)
            except OSError:
                pass
            shutil.copyfile(briefcase_wxs_orig, briefcase_wxs)
        else:
            shutil.copyfile(briefcase_wxs, briefcase_wxs_orig)

        lines = []
        with open(briefcase_wxs) as template:
            for line in template:
                if line.strip() == '<!-- CONTENT -->':
                    lines.extend(content)
                elif line.strip() == '<!-- CONTENTREFS -->':
                    lines.extend(contentrefs)
                elif line.strip() == '<!-- SHORTCUTS -->':
                    lines.extend(shortcuts)
                else:
                    lines.append(line.rstrip())

        with open(briefcase_wxs, 'w') as template:
            for line in lines:
                template.write('{}\n'.format(line))

    def build_app(self):
        print()
        print(" * Looking for WiX Toolset...")
        wix_path = os.getenv('WIX')
        if not wix_path:
            print("Couldn't find WiX Toolset. Please visit:")
            print()
            print("    http://wixtoolset.org/releases/")
            print()
            print("and install the latest stable release.")
            sys.exit(-2)
        else:
            print("   - Using {}".format(wix_path))

        print(" * Compiling application installer...")
        proc = subprocess.Popen(
            [
                os.path.join(wix_path, 'bin', 'candle'),
                "-ext", "WixUtilExtension",
                "briefcase.wxs"
            ],
            cwd=os.path.abspath(self.dir)
        )
        proc.wait()
        if proc.returncode != 0:
            return False

        print(" * Linking application installer...")
        proc = subprocess.Popen(
            [
                os.path.join(wix_path, 'bin', 'light'),
                "-ext", "WixUtilExtension",
                "-ext", "WixUIExtension",
                "-o", "{}-{}.msi".format(self.formal_name, self.version),
                "briefcase.wixobj"
            ],
            cwd=os.path.abspath(self.dir)
        )
        proc.wait()
        return proc.returncode == 0

    def start_app(self):
        print()
        print(" * Starting {}...".format(self.formal_name))
        subprocess.Popen(
            [
                os.path.join('pythonw'),
                os.path.join('..', 'app', 'start.py'),
            ],
            cwd=os.path.join(os.path.abspath(self.dir), 'content', 'python')
        ).wait()
