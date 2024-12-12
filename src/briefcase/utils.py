import os
import re


def _has_url(requirement) -> bool:
    """Determine if the requirement is defined as a URL.

    Detects any of the URL schemes supported by pip
    (https://pip.pypa.io/en/stable/topics/vcs-support/).

    :param requirement: The requirement to check
    :returns: True if the requirement is a URL supported by pip.
    """
    return any(
        f"{scheme}:" in requirement
        for scheme in (
            ["http", "https", "file", "ftp"]
            + ["git+file", "git+https", "git+ssh", "git+http", "git+git", "git"]
            + ["hg+file", "hg+http", "hg+https", "hg+ssh", "hg+static-http"]
            + ["svn", "svn+svn", "svn+http", "svn+https", "svn+ssh"]
            + ["bzr+http", "bzr+https", "bzr+ssh", "bzr+sftp", "bzr+ftp", "bzr+lp"]
        )
    )


def is_local_path(reference) -> bool:
    """Determine if the reference is a local file path.

    :param reference: The reference to check
    :returns: True if the reference is a local file path
    """
    # Windows allows both / and \ as a path separator in references.
    separators = [os.sep]
    if os.altsep:
        separators.append(os.altsep)

    return any(sep in reference for sep in separators) and (not _has_url(reference))


_RELATIVE_PATH_MATCHER = re.compile(r"^\.{1,2}[\\/]")


def is_relative_local_path(reference) -> bool:
    """Determine if the reference is a relative local file path.

    :param reference: The reference to check
    :returns: True if the reference is a relative local file path."""
    return _RELATIVE_PATH_MATCHER.match(reference) is not None and is_local_path(
        reference
    )
