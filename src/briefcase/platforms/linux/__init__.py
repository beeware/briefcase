
DEFAULT_OUTPUT_FORMAT = 'appimage'


class LinuxMixin:
    def __init__(self, output_format):
        super().__init__(platform='linux', output_format=output_format)

    def verify_tools(self):
        pass
