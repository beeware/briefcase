import pkg_resources


def get_platforms():
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('briefcase.platforms')
    }


def get_output_formats(platform):
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('briefcase.formats.{platform}'.format(
            platform=platform
        ))
    }
