"""Jinja2 extensions."""

from jinja2.ext import Extension


class RGBExtension(Extension):
    """Jinja2 extension to convert a hex RGB color to float values."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super(RGBExtension, self).__init__(environment)

        def float_red(obj):
            try:
                return int(obj.lstrip('#')[0:2], 16) / 255.0
            except ValueError:
                return 1.0

        def float_green(obj):
            try:
                return int(obj.lstrip('#')[2:4], 16) / 255.0
            except ValueError:
                return 1.0

        def float_blue(obj):
            try:
                return int(obj.lstrip('#')[4:6], 16) / 255.0
            except ValueError:
                return 1.0

        environment.filters['float_red'] = float_red
        environment.filters['float_green'] = float_green
        environment.filters['float_blue'] = float_blue
