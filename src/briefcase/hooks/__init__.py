from importlib.metadata import entry_points

from briefcase.hooks.base import BaseHook


def get_hooks() -> dict[str, type[BaseHook]]:
    """Load built-in and third-party hook plugins.

    :returns: A dict mapping entry point names to hook classes.
    """
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="briefcase.hooks")
    }
