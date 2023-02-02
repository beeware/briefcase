from briefcase.integrations.xcode import verify_xcode_install

DEFAULT_OUTPUT_FORMAT = "Xcode"


class iOSMixin:
    platform = "iOS"
    supported_host_os = {"Darwin"}
    supported_host_os_reason = (
        "iOS applications require Xcode, which is only available on macOS."
    )

    def verify_tools(self):
        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        verify_xcode_install(self.tools, min_version=(10, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
