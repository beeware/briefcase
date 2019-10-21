
DEFAULT_OUTPUT_FORMAT = 'appimage'


class LinuxMixin:
    def __init__(self, *args, output_format, **kwargs):
        super().__init__(*args, platform='linux', output_format=output_format, **kwargs)

    def verify_tools(self):
        pass
