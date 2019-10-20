
DEFAULT_OUTPUT_FORMAT = 'app'


class MacOSMixin:
    def __init__(self, output_format, *args, **kwargs):
        super().__init__(*args, platform='macos', output_format=output_format, **kwargs)

    def verify_tools(self):
        print("Verify that macOS build tools exist")
