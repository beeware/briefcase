
class BriefcaseError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code


class NoCommandError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(-10)
        self.msg = msg

    def __str__(self):
        return self.msg


class ShowOutputFormats(BriefcaseError):
    def __init__(self, platform, default, choices):
        super().__init__(0)
        self.platform = platform
        self.default = default
        self.choices = choices

    def __str__(self):
        choices = ', '.join(sorted(self.choices))
        return (
            "Available formats for {self.platform}: {choices}\n"
            "Default format: {self.default}".format(
                self=self,
                choices=choices,
            )
        )


class InvalidFormatError(BriefcaseError):
    def __init__(self, requested, choices):
        super().__init__(-21)
        self.requested = requested
        self.choices = choices

    def __str__(self):
        choices = ', '.join(sorted(self.choices))
        return "Invalid format '{self.requested}'; (choose from: {choices})".format(
            self=self,
            choices=choices,
        )


class UnsupportedCommandError(BriefcaseError):
    def __init__(self, platform, output_format, command):
        super().__init__(-30)
        self.platform = platform
        self.output_format = output_format
        self.command = command

    def __str__(self):
        return (
            "The {self.command} command for the {self.platform} {self.output_format} format "
            "has not been implemented (yet!).".format(
                self=self,
            )
        )


class BriefcaseConfigError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(100)
        self.msg = msg

    def __str__(self):
        return "Briefcase configuration error: {self.msg}".format(self=self)


class BriefcaseCommandError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(200)
        self.msg = msg

    def __str__(self):
        return self.msg


class NetworkFailure(BriefcaseCommandError):
    def __init__(self, action):
        self.action = action
        super().__init__(msg="Unable to {action}; is your computer offline?".format(
            action=action
        ))


class MissingNetworkResourceError(BriefcaseCommandError):
    def __init__(self, url):
        self.url = url
        super().__init__(
            msg="Unable to download {url}; is the URL correct?".format(
                url=url
            )
        )


class BadNetworkResourceError(BriefcaseCommandError):
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
        super().__init__(
            msg="Unable to download {url} (status code {status_code})".format(
                url=url,
                status_code=status_code,
            )
        )


class MissingToolError(BriefcaseCommandError):
    def __init__(self, tool):
        self.tool = tool
        super().__init__(
            msg="Unable to locate {tool!r}. Has it been installed?".format(
                tool=tool,
            )
        )
