class BriefcaseError(Exception):
    def __init__(self, error_code, skip_logfile=False):
        self.error_code = error_code
        self.skip_logfile = skip_logfile


class HelpText(BriefcaseError):
    """Exceptions that contain help text and shouldn't be displayed to users as
    an error."""


class InfoHelpText(HelpText):
    def __init__(self, msg):
        super().__init__(error_code=0, skip_logfile=True)
        self.msg = msg

    def __str__(self):
        return self.msg


class NoCommandError(HelpText):
    def __init__(self, msg):
        super().__init__(error_code=-10, skip_logfile=True)
        self.msg = msg

    def __str__(self):
        return self.msg


class ShowOutputFormats(InfoHelpText):
    def __init__(self, platform, default, choices):
        super().__init__(
            f"Available formats for {platform}: {', '.join(sorted(choices))}\n"
            f"Default format: {default}"
        )
        self.platform = platform
        self.default = default
        self.choices = choices


class InvalidFormatError(BriefcaseError):
    def __init__(self, requested, choices):
        super().__init__(error_code=-21, skip_logfile=True)
        self.requested = requested
        self.choices = choices

    def __str__(self):
        choices = ", ".join(sorted(self.choices))
        return f"Invalid format '{self.requested}'; (choose from: {choices})"


class UnsupportedCommandError(BriefcaseError):
    def __init__(self, platform, output_format, command):
        super().__init__(error_code=-30, skip_logfile=True)
        self.platform = platform
        self.output_format = output_format
        self.command = command

    def __str__(self):
        return (
            f"The {self.command} command for the {self.platform} {self.output_format} format "
            "has not been implemented (yet!)."
        )


class BriefcaseConfigError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(error_code=100, skip_logfile=True)
        self.msg = msg

    def __str__(self):
        return f"Briefcase configuration error: {self.msg}"


class BriefcaseCommandError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(error_code=200)
        self.msg = msg

    def __str__(self):
        return self.msg


class NetworkFailure(BriefcaseCommandError):
    def __init__(self, action):
        self.action = action
        super().__init__(msg=f"Unable to {action}; is your computer offline?")


class MissingNetworkResourceError(BriefcaseCommandError):
    def __init__(self, url):
        self.url = url
        super().__init__(msg=f"Unable to download {url}; is the URL correct?")


class BadNetworkResourceError(BriefcaseCommandError):
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
        super().__init__(msg=f"Unable to download {url} (status code {status_code})")


class MissingToolError(BriefcaseCommandError):
    def __init__(self, tool):
        self.tool = tool
        super().__init__(msg=f"Unable to locate {tool!r}. Has it been installed?")


class NonManagedToolError(BriefcaseCommandError):
    def __init__(self, tool):
        self.tool = tool
        super().__init__(msg=f"{tool!r} is using an install that is user managed.")


class InvalidDeviceError(BriefcaseCommandError):
    def __init__(self, id_type, device):
        self.id_type = id_type
        self.device = device
        super().__init__(msg=f"Invalid device {id_type} '{device}'")


class CorruptToolError(BriefcaseCommandError):
    def __init__(self, tool):
        self.tool = tool
        super().__init__(msg=f"{tool!r} found, but it appears to be corrupted.")


class CommandOutputParseError(BriefcaseCommandError):
    def __init__(self, parse_error):
        super().__init__(msg=f"Unable to parse command output: {parse_error}")
