import sys

if sys.version_info >= (3, 10):  # pragma: no-cover-if-lt-py310
    from importlib.metadata import entry_points
else:  # pragma: no-cover-if-gte-py310
    # Before Python 3.10, entry_points did not support the group argument;
    # so, the backport package must be used on older versions.
    from importlib_metadata import entry_points


def get_platforms():
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="briefcase.platforms")
    }


def get_output_formats(platform):
    # The values for output format entry points are the importable module names,
    # which may not match the human-readable name. (e.g., the Xcode format is in
    # the briefcase.platforms.macOS.xcode module). The human-readable names for
    # formats must be extracted from the `output_format` attribute of a command
    # *in* the module; every output format has a `create` command, so we use
    # that.
    output_formats = {}
    for entry_point in entry_points(group=f"briefcase.formats.{platform}"):
        module = entry_point.load()
        output_formats[module.create.output_format] = module

    return output_formats
