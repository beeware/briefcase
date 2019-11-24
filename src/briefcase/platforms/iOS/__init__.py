from briefcase.integrations.xcode import ensure_xcode_is_installed

DEFAULT_OUTPUT_FORMAT = 'xcode'


class iOSMixin:
    def __init__(self, output_format, *args, **kwargs):
        super().__init__(*args, platform='iOS', output_format=output_format, **kwargs)

    def verify_tools(self):
        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        ensure_xcode_is_installed(min_version=(10, 0, 0))
