import argparse
import pkg_resources
import sys

from briefcase import __version__


class BriefcaseCommandError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code


class NoCommandError(BriefcaseCommandError):
    def __init__(self, msg):
        super().__init__(-10)
        self.msg = msg

    def __str__(self):
        return self.msg


class UnknownFormatsError(BriefcaseCommandError):
    def __init__(self):
        super().__init__(-20)

    def __str__(self):
        print(
            'Formats are platform specific. Specify a platform to see availble formats.',
            file=sys.stderr
        )


class ShowOutputFormats(BriefcaseCommandError):
    def __init__(self, platform, default, choices):
        super().__init__(0)
        self.platform = platform
        self.default = default
        self.choices = choices

    def __str__(self):
        choices = ', '.join(sorted(self.choices))
        return (
            f"Available formats for {self.platform}: {choices}\n"
            f"Default format: {self.default}"
        )


class InvalidFormatError(BriefcaseCommandError):
    def __init__(self, requested, choices):
        super().__init__(-21)
        self.requested = requested
        self.choices = choices

    def __str__(self):
        choices = ', '.join(sorted(self.choices))
        return f"Invalid format '{self.requested}'; (choose from: {choices})"


class UnsupportedCommandError(BriefcaseCommandError):
    def __init__(self, platform, output_format, command):
        super().__init__(-30)
        self.platform = platform
        self.output_format = output_format
        self.command = command

    def __str__(self):
        return (
            f"The {self.command} command for the {self.platform} {self.output_format} format "
            "has not been implemented (yet!)."
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
        choices=['create', 'update', 'build', 'run', 'publish'],
        metavar='command',
        nargs='?',
        help='the command to run create/update run (one of: %(choices)s)',
    )

    # <platform> *is* optional, with the default value based on the platform
    # that you're on. We don't use the builtin argparse choices/defulat
    # handling so that we can control the error message handling.
    # It also normalizes case so "macOS" and "macos" are both
    # valid.
    platforms = {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('briefcase.platforms')
    }
    default_platform = {
        'darwin': 'macos',
        'linux': 'linux',
        'win32': 'win32',
    }[sys.platform]
    parser.add_argument(
        'platform',
        choices=list(platforms.keys()),
        metavar='platform',
        nargs='?',
        type=str.lower,
        help=f'The platform to target (one of %(choices)s; default: {default_platform}).'
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

    # Use parse_known_args to ensure any extra arguments can be ignored,
    # and parsed as part of subcommand handling. This will capture the
    # command, platform (filling a default if unspecified) and format
    # (with no value if unspecified).
    options, extra = parser.parse_known_args(args)

    # If no command has been provided, display top-level help.
    if options.command is None:
        raise NoCommandError(parser.format_help())

    # If no platform has been provided, use the default.
    # options.platform is what was explicitly specified
    # platform is what will be implicit used
    if options.platform is None:
        platform = default_platform
    else:
        platform = options.platform

    # Import the platform module
    platform_module = platforms[platform]

    output_formats = {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points(f'briefcase.formats.{platform}')
    }
    # If the user requested a list of available output formats, output them.
    if options.show_output_formats:
        if options.platform is None:
            raise UnknownFormatsError()
        else:
            raise ShowOutputFormats(
                platform=platform,
                default=platform_module.DEFAULT_OUTPUT_FORMAT,
                choices=list(output_formats.keys()),
            )

    # If the output format wasn't explicitly specified, check to see
    # Otherwise, extract and use the default output_format for the platform.
    if options.output_format is None:
        output_format = platform_module.DEFAULT_OUTPUT_FORMAT
    else:
        output_format = options.output_format

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

    # Construct a parser for the remaining arguments.
    # This parser has already consumed the command, platform and format, so
    # these can be absorbed into the program name.
    # This parser sets up some default options.
    command_parser = argparse.ArgumentParser(
        prog=f"briefcase {options.command} {platform} {output_format}",
        description=Command.description,
    )
    command_parser.add_argument(
        '-v', '--verbosity',
        action='count',
        default=1,
        help="set the verbosity of output"
    )
    command_parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__
    )

    return Command(command_parser, extra)


def main():
    try:
        command = parse_cmdline(sys.argv[1:])
        command()
        result = 0
    except BriefcaseCommandError as e:
        print(e, file=sys.stdout if e.error_code == 0 else sys.stderr)
        result = e.error_code

    sys.exit(result)


if __name__ == '__main__':
    main()
