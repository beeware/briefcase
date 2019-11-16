
DEFAULT_OUTPUT_FORMAT = 'xcode'


class iOSMixin:
    def __init__(self, output_format, *args, **kwargs):
        super().__init__(*args, platform='iOS', output_format=output_format, **kwargs)

    def verify_tools(self):
        pass
