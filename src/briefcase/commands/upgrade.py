from __future__ import annotations

import sys
from operator import attrgetter

from briefcase.exceptions import (
    BriefcaseCommandError,
    UnsupportedHostError,
    UpgradeToolError,
)
from briefcase.integrations.base import ManagedTool, Tool, tool_registry

from .base import BaseCommand


class UpgradeCommand(BaseCommand):
    cmd_line = "briefcase upgrade"
    command = "upgrade"
    output_format = None
    description = "Upgrade Briefcase-managed tools."

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
            help="List the Briefcase-managed tools that are currently installed",
        )
        parser.add_argument(
            "tool_list",
            metavar="tool",
            nargs="*",
            help="The Briefcase-managed tool to upgrade. If no tool is named, all tools will be upgraded",
        )

    def get_tools_to_upgrade(self, tool_list: set[str]) -> list[ManagedTool]:
        """Returns set of managed Tools that can be upgraded.

        Raises ``BriefcaseCommandError`` if user list contains any invalid tool names.
        """
        upgrade_list: set[type[Tool]]
        tools_to_upgrade: set[ManagedTool] = set()

        # Validate user tool list against tool registry
        if tool_list:
            if invalid_tools := tool_list - set(tool_registry):
                raise UpgradeToolError(
                    f"Briefcase does not know how to manage {', '.join(sorted(invalid_tools))}."
                )
            upgrade_list = {
                tool for name, tool in tool_registry.items() if name in tool_list
            }
        else:
            upgrade_list = set(tool_registry.values())

        # Filter list of tools to those that are being managed
        for tool_klass in upgrade_list:
            if issubclass(tool_klass, ManagedTool):
                try:
                    tool = tool_klass.verify(tools=self.tools, install=False)
                except (BriefcaseCommandError, UnsupportedHostError):
                    pass
                else:
                    if tool.managed_install:
                        tools_to_upgrade.add(tool)

        # Let the user know if any requested tools are not being managed
        if tool_list:
            if unmanaged_tools := tool_list - {tool.name for tool in tools_to_upgrade}:
                error_msg = (
                    f"Briefcase is not managing {', '.join(sorted(unmanaged_tools))}."
                )
                if not tools_to_upgrade:
                    raise UpgradeToolError(error_msg)
                else:
                    self.logger.warning(error_msg)

        return sorted(list(tools_to_upgrade), key=attrgetter("name"))

    def __call__(self, tool_list: list[str], list_tools: bool = False, **options):
        """Perform tool upgrades or list tools qualifying for upgrade.

        :param tool_list: List of tool names from user to upgrade.
        :param list_tools: Boolean to only list upgradeable tools (default False).
        """
        if tools_to_upgrade := self.get_tools_to_upgrade(set(tool_list)):
            self.logger.info(
                f"Briefcase {'is managing' if list_tools else 'will upgrade'} the following tools:",
                prefix=self.command,
            )
            for tool in tools_to_upgrade:
                self.logger.info(f" - {tool.full_name} ({tool.name})")

            if not list_tools:
                for tool in tools_to_upgrade:
                    self.logger.info(f"Upgrading {tool.full_name}...", prefix=tool.name)
                    tool.upgrade()
        else:
            self.logger.info("Briefcase is not managing any tools.")
