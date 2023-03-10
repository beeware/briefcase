import sys
from typing import List

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.java import JDK
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.wix import WiX

from .base import BaseCommand


class UpgradeCommand(BaseCommand):
    cmd_line = "briefcase upgrade"
    command = "upgrade"
    output_format = None
    description = "Upgrade Briefcase-managed tools."

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.sdks = [
            AndroidSDK,
            LinuxDeploy,
            JDK,
            WiX,
            RCEdit,
        ]

    @property
    def platform(self):
        """The upgrade command always reports as the local platform."""
        return {
            "darwin": "macOS",
            "linux": "linux",
            "win32": "windows",
        }[sys.platform]

    def bundle_path(self, app):
        """A placeholder; Upgrade command doesn't have a bundle path."""
        raise NotImplementedError()

    def binary_path(self, app):
        """A placeholder; Upgrade command doesn't have a binary path."""
        raise NotImplementedError()

    def add_options(self, parser):
        parser.add_argument(
            "-l",
            "--list",
            dest="list_tools",
            action="store_true",
            help="List the Briefcase-managed tools that are currently installed.",
        )
        parser.add_argument(
            "tool_list",
            metavar="tool",
            nargs="*",
            help="The Briefcase-managed tool to upgrade. If no tool is named, all tools will be upgraded.",
        )

    def __call__(self, tool_list: List[str], list_tools=False, **options):
        # Verify all the managed SDKs and plugins to see which are present.
        managed_tools = {}
        non_managed_tools = set()

        for klass in self.sdks:
            try:
                tool = klass.verify(self.tools, install=False)
                if tool.managed_install:
                    managed_tools[klass.name] = tool
                    try:
                        for plugin_klass in tool.plugins.values():
                            try:
                                plugin = plugin_klass.verify(self.tools, install=False)
                                # All plugins are managed
                                managed_tools[plugin.name] = plugin
                            except BriefcaseCommandError:
                                # Plugin doesn't exist
                                non_managed_tools.add(klass.name)
                    except AttributeError:
                        # Tool doesn't have plugins
                        pass
                else:
                    non_managed_tools.add(klass.name)
            except BriefcaseCommandError:
                # Tool doesn't exist
                non_managed_tools.add(klass.name)

        # If a tool list wasn't provided, use the list of installed tools
        if not tool_list:
            tool_list = sorted(managed_tools.keys())

        # Build a list of requested tools that are managed.
        found_tools = []
        for name in tool_list:
            if name in managed_tools:
                found_tools.append(name)
            elif name not in non_managed_tools:
                raise BriefcaseCommandError(
                    f"Briefcase doesn't know how to manage the tool '{name}'"
                )

        if found_tools:
            if list_tools:
                self.logger.info("Briefcase is managing the following tools:")
                for name in found_tools:
                    self.logger.info(f" - {name}")
            else:
                self.logger.info("Briefcase will upgrade the following tools:")
                for name in found_tools:
                    self.logger.info(f" - {name}")

                for name in found_tools:
                    tool = managed_tools[name]
                    self.logger.info(f"Upgrading {tool.full_name}...", prefix=tool.name)
                    tool.upgrade()

        else:
            self.logger.info("Briefcase is not managing any tools.")
