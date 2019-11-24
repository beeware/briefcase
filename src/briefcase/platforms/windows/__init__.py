
DEFAULT_OUTPUT_FORMAT = 'msi'


class WindowsMixin:
    def __init__(self, *args, output_format, **kwargs):
        super().__init__(*args, platform='windows', output_format=output_format, **kwargs)

    def verify_tools(self):
        pass
