"""Jinja2 extensions."""

from jinja2.ext import Extension


class PythonVersionExtension(Extension):
    """Jinja2 extension to convert a full Python version string (3.11.0rc1) into useful
    values."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def py_tag(obj):
            """A Python version tag (3.11)"""
            return ".".join(obj.split(".")[:2])

        def py_libtag(obj):
            """A Python version library tag (311)"""
            return "".join(obj.split(".")[:2])

        environment.filters["py_tag"] = py_tag
        environment.filters["py_libtag"] = py_libtag


class RGBExtension(Extension):
    """Jinja2 extension to convert a hex RGB color to float values."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def float_red(obj):
            try:
                return int(obj.lstrip("#")[:2], 16) / 255.0
            except ValueError:
                return 1.0

        def float_green(obj):
            try:
                return int(obj.lstrip("#")[2:4], 16) / 255.0
            except ValueError:
                return 1.0

        def float_blue(obj):
            try:
                return int(obj.lstrip("#")[4:6], 16) / 255.0
            except ValueError:
                return 1.0

        environment.filters["float_red"] = float_red
        environment.filters["float_green"] = float_green
        environment.filters["float_blue"] = float_blue


class TOMLEscape(Extension):
    """Jinja2 extension to escape strings so TOML don't break."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def escape_toml(obj):
            """Escapes double quotes and backslashes."""
            return obj.replace('"', '"').replace("\\", "\\\\")

        environment.filters["escape_toml"] = escape_toml
