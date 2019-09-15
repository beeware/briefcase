
DEFAULT_OUTPUT_FORMAT = 'app'


class MacOSMixin:
    def __init__(self, output_format):
        super().__init__(platform='macos', output_format=output_format)

    def verify_tools(self):
        print("Verify that macOS build tools exist")
