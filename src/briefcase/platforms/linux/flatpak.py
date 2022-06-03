# An implementation would go here!

# needs system tools: flatpak and flatpak-builder
#
# also I used https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator
# to transform eg: 'requirements.txt' into the "python3-requirements.json"
# 
# but really we want to transform the pyproject.toml directly and to have the
# transformer be a library not a standalone python program.
# 
# commands run:
#
# flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
# flatpak install flathub org.freedesktop.Platform//21.08 org.freedesktop.Sdk//21.08
# pip freeze > requirements.txt
# flatpak-pip-generator --requirements-file=requirements.txt
#
# org.zoic.hello.yaml:
#
#   app-id: org.zoic.hello
#   runtime: org.freedesktop.Platform
#   runtime-version: '21.08'
#   sdk: org.freedesktop.Sdk
#   command: hello.py
#   modules:
#     - name: hello
#       buildsystem: simple
#       build-commands:
#         - install -D hello.py /app/bin/hello.py
#       sources:
#         - type: file
#           path: hello.py
#     - python3-requirements.json
#   finish-args:
#     - "--socket=fallback-x11"
#     - "--socket=wayland"
#
# flatpak-builder --user --install --force-clean build-dir/ org.zoic.hello.yaml
# flatpak run -v org.zoic.hello
#
# and that got the app to pop up on my machine ...
#
# Issues:
# * the flakpak-builder manifest file is either json or yaml, it'll parse JSON
#   from a tempfile or /dev/stdin but it interprets include paths relative so
#   use absolute paths if that's what you want to do.
# * flatpak-builder is in C (!)
# * flatpak-pip-generator is a python program which translates requirements.txt
#   files into includable "python3-requirements.json" module *but* it isn't 
#   distributed on pypi, isn't a library and doesn't load pyproject.toml so I
#   suspect we're better off doing this stuff here instead.


import os
import subprocess
from contextlib import contextmanager

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import verify_docker
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.platforms.linux import LinuxMixin


class LinuxFlatpakMixin(LinuxMixin):
    output_format = "flatpak"

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.AppDir"

    def distribution_path(self, app, packaging_format):
        return self.binary_path(app)


class LinuxFlatpakCreateCommand(LinuxFlatpakMixin, CreateCommand):
    description = "Create and populate a Linux Flatpak."

    def create_app(self, app: BaseConfig, **options):
        raise NotImplementedError("stub")


class LinuxFlatpakUpdateCommand(LinuxFlatpakMixin, UpdateCommand):
    description = "Update an existing Linux Flatpak."


class LinuxFlatpakBuildCommand(LinuxFlatpakMixin, BuildCommand):
    description = "Build a Linux Flatpak."

    def verify_tools(self):
        pass

    def build_app(self, app: BaseConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.logger.info()
        self.logger.info(f"[{app.app_name}] Building Flatpak...")

        raise NotImplementedError("stub")

class LinuxFlatpakRunCommand(LinuxFlatpakMixin, RunCommand):
    description = "Run a Linux Flatpak."

    def verify_tools(self):
        """Verify that we're on Linux."""
        super().verify_tools()
        if self.host_os != "Linux":
            raise BriefcaseCommandError("Flatpaks can only be executed on Linux.")

    def run_app(self, app: BaseConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """

        raise NotImplementedError("stub")


class LinuxFlatpakPackageCommand(LinuxFlatpakMixin, PackageCommand):
    description = "Publish a Linux Flatpak."


class LinuxFlatpakPublishCommand(LinuxFlatpakMixin, PublishCommand):
    description = "Publish a Linux Flatpak."


# Declare the briefcase command bindings
create = LinuxFlatpakCreateCommand  # noqa
update = LinuxFlatpakUpdateCommand  # noqa
build = LinuxFlatpakBuildCommand  # noqa
run = LinuxFlatpakRunCommand  # noqa
package = LinuxFlatpakPackageCommand  # noqa
publish = LinuxFlatpakPublishCommand  # noqa
