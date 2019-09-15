
DEFAULT_OUTPUT_FORMAT = 'msi'


class WindowsMixin:
    def __init__(self, output_format):
        super().__init__(platform='windows', output_format=output_format)

    def verify_tools(self):
        pass
