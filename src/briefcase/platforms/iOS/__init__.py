from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import ensure_xcode_is_installed

DEFAULT_OUTPUT_FORMAT = 'xcode'


class iOSMixin:
    platform = 'iOS'

    def verify_tools(self):
        super().verify_tools()
        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
iOS applications require Xcode, which is only available on macOS.
""")

        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        ensure_xcode_is_installed(min_version=(10, 0, 0))
