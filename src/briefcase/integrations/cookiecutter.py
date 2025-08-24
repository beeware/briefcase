"""Jinja2 extensions."""

import re
import uuid
from xml.sax.saxutils import escape, quoteattr

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

        def nuget_version(obj):
            """A Python version in Nuget format (3.14.0-rc1)."""
            parts = obj.split(".")[:3]
            if not parts[2].isnumeric():
                parts[2] = re.sub(r"(\d+)", r"\1-", parts[2], count=1)
            return ".".join(parts)

        environment.filters["py_tag"] = py_tag
        environment.filters["py_libtag"] = py_libtag
        environment.filters["nuget_version"] = nuget_version


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
            return obj.replace("\\", "\\\\").replace('"', '\\"')

        def escape_non_ascii(obj):
            """Quotes obj if non ascii characters are present."""
            if obj.isascii():
                return obj
            else:
                return '"' + obj + '"'

        environment.filters["escape_toml"] = escape_toml
        environment.filters["escape_non_ascii"] = escape_non_ascii


class GradleEscape(Extension):
    """Jinja2 extension to escape strings for Gradle as well."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def escape_gradle(obj):
            """Escapes single quotes and backslashes."""
            return obj.replace("\\", "\\\\").replace("'", "\\'")

        def escape_non_ascii(obj):
            """Quotes obj if non ascii characters are present."""
            if obj.isascii():
                return obj
            else:
                return '"' + obj + '"'

        environment.filters["escape_gradle"] = escape_gradle
        environment.filters["escape_non_ascii"] = escape_non_ascii


class PListExtension(Extension):
    """Jinja2 extension for generating plist values."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def plist_value(obj):
            """Render value in plist format."""
            if isinstance(obj, bool):
                if obj:
                    return "<true/>"
                else:
                    return "<false/>"
            elif isinstance(obj, list):
                children = "\n        ".join(plist_value(value) for value in obj)
                return f"<array>\n        {children}\n    </array>"
            elif isinstance(obj, dict):
                children = "\n        ".join(
                    f"<key>{key}</key>\n        {plist_value(value)}"
                    for key, value in obj.items()
                )
                return f"<dict>\n        {children}\n    </dict>"
            else:
                return f"<string>{obj}</string>"

        environment.filters["plist_value"] = plist_value


class XMLExtension(Extension):
    """Jinja2 extension for generating XML values."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def bool_attr(obj):
            """Render value in XML format appropriate for an attribute."""
            return "true" if obj else "false"

        def xml_escape(obj):
            """Filter to escape characters <, >, &, " and '."""
            return escape(obj)

        def xml_attr(obj):
            """ "Filter to quote an XML value appropriately."""
            return quoteattr(obj)

        environment.filters["bool_attr"] = bool_attr
        environment.filters["xml_escape"] = xml_escape
        environment.filters["xml_attr"] = xml_attr


class UUIDExtension(Extension):
    """Extensions for generating UUIDs."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)

        def dns_uuid5(obj):
            """A DNS-based UUID5 object generated from the provided content."""
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, obj))

        environment.filters["dns_uuid5"] = dns_uuid5
