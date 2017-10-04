import distutils.command.install_scripts as orig
import os
from pkg_resources import Distribution, PathMetadata
import re
import shutil
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

        iconfile = '%s.ico' % self.icon
        self.icon_filename = os.path.join(self.app_dir, self.distribution.get_name() + os.path.splitext(iconfile)[1])

    def generate_app_template(self, extra_context=None):
        if self.version_numeric != self.version and not self.sanitize_version:
            print(" ! Windows Installer version can only contain numerals, currently: %s" % self.version)
            print(" ! --sanitize-version can be used to automatically filter this to %s" % self.version_numeric)
            exit(1)

        super(windows, self).generate_app_template(extra_context=extra_context)

    def install_icon(self):
        shutil.copyfile('%s.ico' % self.icon, self.icon_filename)

    def install_splash(self):
        raise RuntimeError("Windows doesn't support splash screens.")

    def find_support_pkg(self):
        version = "%s.%s.%s" % sys.version_info[:3]
        return 'https://www.python.org/ftp/python/%s/python-%s-embed-amd64.zip' % (version, version)

    def install_extras(self):
        print(" * Finalizing application installer script...")

        # Find all the files that need to be put in the installer
        app_root = os.path.join(self.dir, 'content')
        content = []
        contentrefs = []

        def walk_dir(path, depth=0):
            files = []
            parts = path[len(app_root) + 1:].split(os.path.sep)
            for name in os.listdir(path):
                full_path = os.path.join(path, name)

                if parts[0]:
                    full_parts = parts + [name]
                else:
                    full_parts = [name]
                dir_id = '.'.join(re.sub('[^A-Za-z0-9_]', '_', p) for p in full_parts)

                if os.path.isdir(full_path):
                    content.append(
                        '    ' * (depth + 5) + '<Directory Id="DIR_%s" Name="%s">' % (
                            dir_id, name
                        )
                    )
                    walk_dir(os.path.join(path, name), depth=depth + 1)

                    content.append('    ' * (depth + 5) + '</Directory>')
                else:
                    files.append(name)

            if files:
                guid = uuid.uuid4()

                content.append('    ' * (depth + 5) + '<Component Id="COMP_%s" Guid="%s">' % (
                    guid.hex, guid)
                )
                for file in files:
                    content.append('    ' * (depth + 6) + '<File Id="FILE_%s" Source="content/%s/%s" />' % (
                            uuid.uuid4().hex, '/'.join(parts), file
                        )
                    )
                content.append('    ' * (depth + 5) + '</Component>')
                contentrefs.append('            <ComponentRef Id="COMP_%s"/>' % guid.hex)


        walk_dir(app_root)

        # Generate the full briefcase.wxs file
        lines = []
        with open(os.path.join(self.dir, 'briefcase.wxs')) as template:
            for line in template:
                if line.strip() == '<!-- CONTENT -->':
                    lines.extend(content)
                elif line.strip() == '<!-- CONTENTREFS -->':
                    lines.extend(contentrefs)
                else:
                    lines.append(line.rstrip())

        with open(os.path.join(self.dir, 'briefcase.wxs'), 'w') as template:
            for line in lines:
                template.write('%s\n' % line)

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
            print("   - Using %s" % wix_path)

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
                "-o", "%s-%s.msi" % (self.formal_name, self.version),
                "briefcase.wixobj"
            ],
            cwd=os.path.abspath(self.dir)
        )
        proc.wait()
        return proc.returncode == 0

    def start_app(self):
        print()
        print(" * Starting %s..." % self.formal_name)
        subprocess.Popen(
            [
                os.path.join('pythonw'),
                os.path.join('..', 'app', 'start.py'),
            ],
            cwd=os.path.join(os.path.abspath(self.dir), 'content', 'python')
        ).wait()
