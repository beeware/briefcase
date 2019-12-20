import pkg_resources


def get_platforms():
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('briefcase.platforms')
    }


def get_output_formats(platform):
    # Entry point section identifiers (briefcase.formats.macos) are always
    # in lower case, regardless of how they're registered. However, the
    # actual entry point names preserve case.
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('briefcase.formats.{platform}'.format(
            platform=platform.lower()
        ))
    }
