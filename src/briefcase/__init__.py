__all__ = [
    "__version__",
]

try:
    # Read version from SCM metadata
    # This will only exist in a development environment
    from setuptools_scm import get_version

    __version__ = get_version()
except ModuleNotFoundError:
    # Read version from the installer metadata
    from importlib.metadata import version

    __version__ = version("briefcase")
