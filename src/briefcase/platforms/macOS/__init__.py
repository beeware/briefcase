from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import verify_command_line_tools_install

DEFAULT_OUTPUT_FORMAT = 'dmg'


class macOSMixin:
    platform = 'macOS'

    def verify_tools(self):
        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
macOS applications require the Xcode command line tools, which are
only available on macOS.
""")
        # Require the XCode command line tools.
        verify_command_line_tools_install(self)

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
