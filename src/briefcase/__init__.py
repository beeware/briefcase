from importlib.metadata import version

__all__ = [
    "__version__",
]

# Read version from SCM metadata
__version__ = version("briefcase")
