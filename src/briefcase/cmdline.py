import argparse
import sys
from pathlib import Path

from briefcase import __version__
from briefcase.commands import DevCommand, NewCommand, UpgradeCommand
from briefcase.platforms import get_output_formats, get_platforms

from .exceptions import (
    InvalidFormatError,
    NoCommandError,
    ShowOutputFormats,
    UnsupportedCommandError
)


def parse_cmdline(args):
    parser = argparse.ArgumentParser(
        prog="briefcase",
        description="Package Python code for distribution.",
        usage="briefcase [-h] <command> [<platform>] [<format>] ...",
        epilog="Each command, platform and format has additional options. "
               "Use the -h option on a specific command for more details.",
        add_help=False
    )
    parser.add_argument(
        '-f', '--formats',
        action='store_true',
        dest='show_output_formats',
        help="show the available output formats and exit (specify a platform for more details)."
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__
    )

    # <command> isn't actually optional; but if it's marked as required,
    # there's no way to get help for subcommands. So; treat <command>
    # as optional, handle the case where <command> isn't provided
    # as the case where top-level help is displayed, and provide an explicit
    # usage string so that the instructions displayed are correct
    parser.add_argument(
        'command',
        choices=[
            'new', 'dev', 'upgrade',
            'create', 'update', 'build', 'run', 'package', 'publish'
        ],
        metavar='command',
        nargs='?',
        help='the command to execute (one of: %(choices)s)',
    )

    # <platform> *is* optional, with the default value based on the platform
    # that you're on.
    platforms = get_platforms()

    # To make the UX a little forgiving, we normalize *any* case to the case
    # actually used to register the platform. This function maps the lower-case
    # version of the registered name to the actual registered name.
    def normalize(name):
        return {
            n.lower(): n
            for n in platforms.keys()
        }.get(name.lower(), name)

    # Use parse_known_args to ensure any extra arguments can be ignored,
    # and parsed as part of subcommand handling. This will capture the
    # command, platform (filling a default if unspecified) and format
    # (with no value if unspecified).
    options, extra = parser.parse_known_args(args)

    # If no command has been provided, display top-level help.
    if options.command is None:
        raise NoCommandError(parser.format_help())
    elif options.command == 'new':
        command = NewCommand(base_path=Path.cwd())
        options = command.parse_options(
            extra=extra
        )
        return command, options
    elif options.command == 'dev':
        command = DevCommand(base_path=Path.cwd())
        options = command.parse_options(
            extra=extra
        )
        return command, options
    elif options.command == 'upgrade':
        command = UpgradeCommand(base_path=Path.cwd())
        options = command.parse_options(
            extra=extra
        )
        return command, options

    parser.add_argument(
        'platform',
        choices=list(platforms.keys()),
        default={
            'darwin': 'macOS',
            'linux': 'linux',
            'win32': 'windows',
        }[sys.platform],
        metavar='platform',
        nargs='?',
        type=normalize,
        help='The platform to target (one of %(choices)s; default: %(default)s',
    )

    # <format> is also optional, with the default being platform dependent.
    # There's no way to encode option-dependent choices, so allow *any*
    # input, and we'll manually validate.
    parser.add_argument(
        'output_format',
        metavar='format',
        nargs='?',
        help='The output format to use (the available output formats are platform dependent)'
    )

    # Re-parse the aruments, now that we know it is a command that makes use
    # of platform/output_format.
    options, extra = parser.parse_known_args(args)

    # Import the platform module
    platform_module = platforms[options.platform]

    output_formats = get_output_formats(options.platform)
    # If the user requested a list of available output formats, output them.
    if options.show_output_formats:
        raise ShowOutputFormats(
            platform=options.platform,
            default=platform_module.DEFAULT_OUTPUT_FORMAT,
            choices=list(output_formats.keys()),
        )

    # If the output format wasn't explicitly specified, check to see
    # Otherwise, extract and use the default output_format for the platform.
    if options.output_format is None:
        output_format = platform_module.DEFAULT_OUTPUT_FORMAT
    else:
        output_format = options.output_format

    # Normalise casing of output_format to be more forgiving.
    output_format = {
        n.lower(): n for n in output_formats
    }.get(output_format.lower(), output_format)

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
            command=options.command
        )

    # Construct a command, and parse the remaining arguments.
    command = Command(base_path=Path.cwd())
    options = command.parse_options(
        extra=extra
    )
    return command, options
