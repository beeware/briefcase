try:
    # Usually, the pattern is "import module; if it doesn't exist,
    # import the shim". However, we need the 3.10 API for entry_points,
    # as the 3.8 didn't support the `groups` argument to entry_points.
    # Therefore, we try to import the compatibility shim first; and fall
    # back to the stdlib module if the shim isn't there.
    from importlib_metadata import entry_points
except ImportError:
    from importlib.metadata import entry_points


def get_platforms():
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="briefcase.platforms")
    }


def get_output_formats(platform):
    # Entry point section identifiers (briefcase.formats.macos) are always
    # in lower case, regardless of how they're registered. However, the
    # actual entry point names preserve case.
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group=f"briefcase.formats.{platform.lower()}")
    }
