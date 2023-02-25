import sys
from operator import attrgetter
from typing import Collection, List, Set

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, tool_registry

from .base import BaseCommand


def stringify(
    coll: Collection[str],
    prefix: str = "tool",
    plural: str = "",
    conjunction: str = "or",
):
    """Create a user-facing string from a list of strings.

    For instance:
        Inputs:
            coll: ["one", "two", "three"]
            prefix: "number"
            conjunction: "and"
        Output:
            "numbers 'one', 'two', and 'three'"
    :param coll: Collection of strings to stringify
    :param prefix: Noun that describes the strings
    :param plural: Plural version of noun; assumes adding 's' is enough if not specified.
    :param conjunction: Value to use to join the last string to the list; defaults to 'or'.
    """
    comma_list = ", ".join(f"'{val}'" for val in coll)
    if len(coll) > 1:
        prefix = plural or f"{prefix}s"
    return f"{prefix} {f', {conjunction}'.join(comma_list.rsplit(',', 1))}"


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
            help="List the Briefcase-managed tools that are currently installed.",
        )
        parser.add_argument(
            "tool_list",
            metavar="tool",
            nargs="*",
            help="The Briefcase-managed tool to upgrade. If no tool is named, all tools will be upgraded.",
        )

    def get_tools_to_upgrade(self, tool_list: Set[str]) -> List[Tool]:
        """Returns set of Tools that can be upgraded.

        Raises `BriefcaseCommandError` if user list contains any invalid tool names.
        """
        # Validate user tool list against tool registry
        if tool_list:
            if invalid_tools := tool_list - set(tool_registry):
                raise BriefcaseCommandError(
                    f"Briefcase does not know how to manage {stringify(invalid_tools)}."
                )
            upgrade_list = {
                tool for name, tool in tool_registry.items() if name in tool_list
            }
        else:
            upgrade_list = set(tool_registry.values())

        # Filter list of tools to those that are being managed
        tools_to_upgrade = set()
        for tool_klass in upgrade_list:
            try:
                tool = tool_klass.verify(self.tools, install=False, app=object())
            except (BriefcaseCommandError, TypeError, FileNotFoundError):
                # BriefcaseCommandError: Tool isn't installed
                # TypeError: Signature of tool.verify() was incomplete
                # FileNotFoundError: An executable for subprocess.run() was not found
                pass
            else:
                if tool.managed_install:
                    tools_to_upgrade.add(tool)

        # Let the user know if any requested tools are not being managed
        if tool_list:
            if unmanaged_tools := tool_list - {tool.name for tool in tools_to_upgrade}:
                error_msg = f"Briefcase is not managing {stringify(unmanaged_tools)}."
                if not tools_to_upgrade:
                    raise BriefcaseCommandError(error_msg)
                else:
                    self.logger.warning(error_msg)

        return sorted(list(tools_to_upgrade), key=attrgetter("name"))

    def __call__(self, tool_list: List[str], list_tools: bool = False, **options):
        """Perform tool upgrades or list tools qualifying for upgrades.

        :param tool_list: List of tool names. from user to upgrade.
        :param list_tools: Boolean to only list upgradeable tools (default False).
        """
        tool_list = set(tool_list)
        tools_to_upgrade = self.get_tools_to_upgrade(tool_list)

        if tools_to_upgrade:
            action = "is managing" if list_tools else "will upgrade"
            self.logger.info(
                f"Briefcase {action} the following tools:", prefix=self.command
            )
            for tool in tools_to_upgrade:
                self.logger.info(f" - {tool.full_name} ({tool.name})")

            if not list_tools:
                for tool in tools_to_upgrade:
                    self.logger.info(f"Upgrading {tool.full_name}...", prefix=tool.name)
                    tool.upgrade()
        else:
            self.logger.info("Briefcase is not managing any tools.")
