from briefcase.integrations.xcode import Xcode

DEFAULT_OUTPUT_FORMAT = "Xcode"


class iOSMixin:
    platform = "iOS"
    supported_host_os = {"Darwin"}
    supported_host_os_reason = (
        "iOS applications require Xcode, which is only available on macOS."
    )
    # 0.3.16 introduced new-style dylib support.
    platform_target_version = "0.3.16"

    def verify_tools(self):
        Xcode.verify(self.tools, min_version=(13, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
