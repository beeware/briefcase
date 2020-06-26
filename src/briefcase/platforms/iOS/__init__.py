from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import verify_xcode_install

DEFAULT_OUTPUT_FORMAT = 'xcode'


class iOSMixin:
    platform = 'iOS'

    def verify_tools(self):
        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
iOS applications require Xcode, which is only available on macOS.
""")
        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        verify_xcode_install(self, min_version=(10, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
