from __future__ import annotations

import argparse
import sys
from argparse import RawDescriptionHelpFormatter

from briefcase import __version__
from briefcase.commands import (
    BuildCommand,
    ConvertCommand,
    CreateCommand,
    DevCommand,
    NewCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
    UpgradeCommand,
)
from briefcase.commands.base import split_passthrough
from briefcase.console import MAX_TEXT_WIDTH, Console
from briefcase.platforms import get_output_formats, get_platforms

from .exceptions import (
    InvalidFormatError,
    InvalidPlatformError,
    NoCommandError,
    UnsupportedCommandError,
)

COMMANDS = [
    NewCommand,
    DevCommand,
    ConvertCommand,
    CreateCommand,
    OpenCommand,
    BuildCommand,
    UpdateCommand,
    RunCommand,
    PackageCommand,
    PublishCommand,
    UpgradeCommand,
]


def parse_cmdline(args, console: Console | None = None):
    """Parses the command line to determine the Command and its arguments.

    :param args: the arguments provided at the command line
    :param console: interface for interacting with the console
    :return: Command and command-specific arguments
    """
    if console is None:
        console = Console()

    platforms = get_platforms()

    briefcase_description = (
        "Briefcase is a tool for converting a Python project "
        "into a standalone native application for distribution."
    )

    description_max_pad_len = max(len(cmd.command) for cmd in COMMANDS) + 2
    command_description_list = "\n".join(
        f"  {cmd.command}{' ' * (description_max_pad_len - len(cmd.command))}{cmd.description}"
        for cmd in COMMANDS
    )

    platform_list = ", ".join(sorted(platforms, key=str.lower))

    additional_instruction = (
        "Each command, platform, and format has additional options. "
        "Use the -h option on a specific command for more details."
    )

    parser = argparse.ArgumentParser(
        prog="briefcase",
        description=console.textwrap(
            f"{briefcase_description}\n"
            "\n"
            "Commands:\n"
            f"{command_description_list}\n"
            "\n"
            "Platforms:\n"
            f"  {platform_list}\n"
            "\n"
            f"{additional_instruction}"
        ),
        usage="briefcase [-h] <command> [<platform>] [<format>] ...",
        add_help=False,
        formatter_class=(
            lambda prog: RawDescriptionHelpFormatter(prog, width=MAX_TEXT_WIDTH)
        ),
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    # <command> isn't actually optional; but if it's marked as required,
    # there's no way to get help for subcommands. So; treat <command>
    # as optional, handle the case where <command> isn't provided
    # as the case where top-level help is displayed, and provide an explicit
    # usage string so that the instructions displayed are correct
    parser.add_argument(
        "command",
        choices=list(cmd.command for cmd in COMMANDS),
        metavar="command",
        nargs="?",
        help=argparse.SUPPRESS,
    )

    # argparse handles `--` specially, so make the passthrough args bypass the parser.
    def parse_known_args(args):
        args, passthrough = split_passthrough(args)
        options, extra = parser.parse_known_args(args)
        if passthrough:
            extra += ["--"] + passthrough
        return options, extra

    # Use parse_known_args to ensure any extra arguments can be ignored,
    # and parsed as part of subcommand handling. This will capture the
    # command, platform (filling a default if unspecified) and format
    # (with no value if unspecified).
    options, extra = parse_known_args(args)

    # If no command has been provided, display top-level help.
    if options.command is None:
        raise NoCommandError(parser.format_help())

    # Commands agnostic to the platform and format
    if options.command == "convert":
        Command = ConvertCommand
    elif options.command == "new":
        Command = NewCommand
    elif options.command == "dev":
        Command = DevCommand
    elif options.command == "upgrade":
        Command = UpgradeCommand
    else:
        # Commands dependent on the platform and format. The general form of such a
        # command is `briefcase <cmd> <platform> <format>`; but the format will be
        # inferred from the platform if one isn't specified, and the platform will be
        # inferred from the operating system if it isn't explicitly given.
        #
        # <platform> and <format> aren't parsed as regular arguments due to ambiguities
        # in interpreting those arguments; instead, they're handled directly from the
        # argument list, with the expectation that they *must* be the first and second
        # arguments (after the command) if provided. There's no other bare arguments, so
        # we only need to look for whether the arguments start with "-".
        if extra and not extra[0].startswith("-"):
            name = extra.pop(0)
            # Normalize the platform name to the registered capitalization
            platform = {n.lower(): n for n in platforms.keys()}.get(name.lower(), name)
        else:
            platform = {
                "darwin": "macOS",
                "linux": "linux",
                "win32": "windows",
            }[sys.platform]

        # Import the platform module
        try:
            platform_module = platforms[platform]
        except KeyError:
            raise InvalidPlatformError(platform, platforms.keys())

        # If the output format wasn't explicitly specified, check to see
        # Otherwise, extract and use the default output_format for the platform.
        if extra and not extra[0].startswith("-") and not extra[0] == "--":
            output_format = extra.pop(0)
        else:
            output_format = platform_module.DEFAULT_OUTPUT_FORMAT

        output_formats = get_output_formats(platform)

        # Normalise casing of output_format to be more forgiving.
        output_format = {n.lower(): n for n in output_formats}.get(
            output_format.lower(), output_format
        )

        # We now know the command, platform, and format.
        # Get the command class that corresponds to that definition.
        try:
            format_module = output_formats[output_format]
            Command = getattr(format_module, options.command)
        except KeyError:
            raise InvalidFormatError(
                requested=output_format,
                choices=list(output_formats.keys()),
            )
        except AttributeError:
            raise UnsupportedCommandError(
                platform=platform,
                output_format=output_format,
                command=options.command,
            )

    return Command, extra
