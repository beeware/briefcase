
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
            "Available formats for {platform}: {choices}\n"
            "Default format: {default}".format(
                platform=self.platform,
                choices=choices,
                default=self.default,
            )
        )


class InvalidFormatError(BriefcaseError):
    def __init__(self, requested, choices):
        super().__init__(-21)
        self.requested = requested
        self.choices = choices

    def __str__(self):
        choices = ', '.join(sorted(self.choices))
        return "Invalid format '{requested}'; (choose from: {choices})".format(
            requested=self.requested,
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
            "The {command} command for the {platform} {output_format} format "
            "has not been implemented (yet!).".format(
                command=self.command,
                platform=self.platform,
                output_format=self.output_format,
            )
        )


class BriefcaseConfigError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(100)
        self.msg = msg


class BriefcaseCommandError(BriefcaseError):
    def __init__(self, msg):
        super().__init__(200)
        self.msg = msg


class NetworkFailure(BriefcaseCommandError):
    def __init__(self, action):
        self.action = action
        super().__init__(msg="Uunable to {action}; is your computer offline?".format(
            action=action
        ))
