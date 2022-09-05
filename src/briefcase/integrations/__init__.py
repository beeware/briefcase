from . import cookiecutter  # TODO: is this being used anywhere???
from . import (
    android_sdk,
    docker,
    flatpak,
    git,
    java,
    linuxdeploy,
    rcedit,
    subprocess,
    visualstudio,
    wix,
    xcode,
)


class ToolCache:
    def __init__(self):
        # Tool wrappers with interfaces
        self.android_sdk = None
        self.docker = None
        self.flatpak = None
        self.git = None
        self.jdk = None
        self.linuxdeploy = None
        self.rcedit = None
        self.visualstudio = None
        self.wix = None

        # Flags for whether a tool is verified
        self._xcode = False
        self._xcode_cli = False

        # App specific tools
        self._current_app = None
        self.build_subprocess = None

    def verify_android_sdk(self, command, install=True):
        if not self.android_sdk:
            self.android_sdk = android_sdk.AndroidSDK.verify(
                command=command,
                install=install,
            )

    def verify_build_subprocess(self, command, app):
        # TODO: currently an identity check since i dont know how Apps do equality checks
        if self._current_app is not app or not self.build_subprocess:
            self.build_subprocess = command.prepare_build_environment(app)
            self._current_app = app

    def cookiecutter(self):
        pass

    def verify_docker(self, command):
        if not self.docker:
            self.docker = docker.verify_docker(command=command)

    def verify_flatpak(self, command):
        if not self.flatpak:
            self.flatpak = flatpak.Flatpak.verify(command=command)

    def verify_git(self, command):
        if not self.git:
            self.git = git.verify_git_is_installed(command=command)

    def verify_java(self, command, install=True):
        if not self.jdk:
            self.jdk = java.JDK.verify(command=command, install=install)

    def verify_linuxdeploy(self, command, install=True, **kwargs):
        if not self.linuxdeploy:
            self.linuxdeploy = linuxdeploy.LinuxDeploy.verify(
                command=command,
                install=install,
                **kwargs,
            )

    def verify_rcedit(self, command, install=True):
        if not self.rcedit:
            self.rcedit = rcedit.RCEdit.verify(command=command, install=install)

    def verify_visualstudio(self, command):
        if not self.visualstudio:
            self.visualstudio = visualstudio.VisualStudio.verify(command=command)

    def verify_xcode(self, command, min_version=None):
        if not self._xcode:
            self._xcode = xcode.verify_xcode_install(
                command=command, min_version=min_version
            )

    def verify_xcode_command_line_tools(self, command):
        if not self._xcode_cli:
            self._xcode_cli = xcode.verify_command_line_tools_install(command=command)

    def verify_wix(self, command, install=True):
        if not self.wix:
            self.wix = wix.WiX.verify(command=command, install=install)


__all__ = [
    "ToolCache",
    "android_sdk",
    "cookiecutter",
    "docker",
    "flatpak",
    "git",
    "java",
    "linuxdeploy",
    "rcedit",
    "subprocess",
    "visualstudio",
    "wix",
    "xcode",
]
