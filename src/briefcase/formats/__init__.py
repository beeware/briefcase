from __future__ import annotations

import operator
from importlib.metadata import entry_points

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats.base import BasePackagingFormat, PackageCommandAPI


def get_packaging_formats(
    platform: str,
    output_format: str,
) -> dict[str, type[BasePackagingFormat]]:
    """Load built-in and third-party packaging formats for a platform/format.

    :param platform: The target platform (e.g., "macOS")
    :param output_format: The output format (e.g., "app")
    :returns: A dict mapping format names to packaging format classes.
    """
    return {
        ep.name: ep.load()
        for ep in entry_points(group=f"briefcase.formats.{platform}.{output_format}")
    }


def get_all_packaging_formats(
    platform: str,
) -> dict[str, type[BasePackagingFormat]]:
    """Load all built-in and third-party packaging formats for a platform.

    Discovered across all output formats for the platform.

    :param platform: The target platform (e.g., "macOS")
    :returns: A dict mapping format names to packaging format classes.
    """
    formats = {}
    for ep in entry_points():
        if ep.group.startswith(f"briefcase.formats.{platform}."):
            formats[ep.name] = ep.load()
    return formats


def get_packaging_format(
    name: str,
    platform: str,
    output_format: str,
    command: PackageCommandAPI,
) -> BasePackagingFormat:
    """Get a packaging format by name for a platform/format.

    :param name: The packaging format name
    :param platform: The target platform
    :param output_format: The output format
    :param command: The command instance
    :returns: An instantiated packaging format.
    """
    formats = get_packaging_formats(platform, output_format)
    if name not in formats:
        # Fallback to searching all formats for the platform if it's not
        # in the current output format.
        formats = get_all_packaging_formats(platform)

    try:
        return formats[name](command=command)
    except KeyError:
        available = ", ".join(sorted(formats)) or "none"
        raise BriefcaseCommandError(
            f"Unknown packaging format: {name}\n\n"
            f"Available formats for {platform}/{output_format}: {available}"
        ) from None


def get_default_packaging_format(
    platform: str,
    output_format: str,
    app: AppConfig,
    command: PackageCommandAPI,
) -> str:
    """Determine the default packaging format for an app.

    :param platform: The target platform
    :param output_format: The output format
    :param app: The app configuration
    :param command: The command instance
    :returns: The name of the default packaging format.
    """
    formats = get_packaging_formats(platform, output_format)
    # Instantiate each format and check its priority
    priorities = {}
    for name, format_class in formats.items():
        try:
            priority = format_class(command=command).priority(app)
            if priority > 0:
                priorities[name] = priority
        except Exception:
            # If priority check fails, ignore this format
            pass

    if not priorities:
        raise BriefcaseCommandError(
            f"No packaging formats are available for {platform}/{output_format}."
        )

    # Return the name of the format with the highest priority.
    # If there's a tie, the first one in sorted order wins.
    return max(sorted(priorities.items()), key=operator.itemgetter(1))[0]
