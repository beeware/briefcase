import argparse
import shutil
import sys
import textwrap
from argparse import RawDescriptionHelpFormatter

from briefcase import __version__
from briefcase.commands import (
    BuildCommand,
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
from briefcase.platforms import get_output_formats, get_platforms

from .exceptions import InvalidFormatError, NoCommandError, UnsupportedCommandError

COMMANDS = [
    NewCommand,
    DevCommand,
    CreateCommand,
    OpenCommand,
    BuildCommand,
    UpdateCommand,
    RunCommand,
    PackageCommand,
    PublishCommand,
    UpgradeCommand,
]


def parse_cmdline(args):
    """Parses the command line to determine the Command and its arguments.

    :param args: the arguments provided at the command line
    :return: Command and command-specific arguments
    """
    platforms = get_platforms()
    width = max(min(shutil.get_terminal_size().columns, 80) - 2, 20)

    briefcase_description = textwrap.fill(
        "Briefcase is a tool for converting a Python project "
        "into a standalone native application for distribution.",
        width=width,
    )

    description_max_pad_len = max(len(cmd.command) for cmd in COMMANDS) + 2
    command_description_list = "\n".join(
        f"  {cmd.command}{' ' * (description_max_pad_len - len(cmd.command))}{cmd.description}"
        for cmd in COMMANDS
    )

    platform_list = ", ".join(sorted(platforms, key=str.lower))

    additional_instruction = textwrap.fill(
        "Each command, platform, and format has additional options. "
        "Use the -h option on a specific command for more details.",
        width=width,
    )

    parser = argparse.ArgumentParser(
        prog="briefcase",
        description=(
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
        formatter_class=lambda prog: RawDescriptionHelpFormatter(prog, width=width),
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

    # To make the UX a little forgiving, we normalize *any* case to the case
    # actually used to register the platform. This function maps the lower-case
    # version of the registered name to the actual registered name.
    def normalize(name):
        return {n.lower(): n for n in platforms.keys()}.get(name.lower(), name)

    # argparse handles `--` specially, so make the passthrough args bypass the parser.
    def parse_known_args(args):
        args, passthough = split_passthrough(args)
        options, extra = parser.parse_known_args(args)
        if passthough:
            extra += ["--"] + passthough
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
    if options.command == "new":
        Command = NewCommand
    elif options.command == "dev":
        Command = DevCommand
    elif options.command == "upgrade":
        Command = UpgradeCommand

    # Commands dependent on the platform and format
    else:
        parser.add_argument(
            "platform",
            choices=list(platforms.keys()),
            default={
                "darwin": "macOS",
                "linux": "linux",
                "win32": "windows",
            }[sys.platform],
            metavar="platform",
            nargs="?",
            type=normalize,
            help="The platform to target (one of %(choices)s; default: %(default)s",
        )

        # <format> is also optional, with the default being platform dependent.
        # There's no way to encode option-dependent choices, so allow *any*
        # input, and we'll manually validate.
        parser.add_argument(
            "output_format",
            metavar="format",
            nargs="?",
            help="The output format to use (the available output formats are platform dependent)",
        )

        # Re-parse the arguments, now that we know it is a command that makes use
        # of platform/output_format.
        options, extra = parse_known_args(args)

        # Import the platform module
        platform_module = platforms[options.platform]

        # If the output format wasn't explicitly specified, check to see
        # Otherwise, extract and use the default output_format for the platform.
        if options.output_format is None:
            output_format = platform_module.DEFAULT_OUTPUT_FORMAT
        else:
            output_format = options.output_format

        output_formats = get_output_formats(options.platform)

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
                platform=options.platform,
                output_format=output_format,
                command=options.command,
            )

    return Command, extra
