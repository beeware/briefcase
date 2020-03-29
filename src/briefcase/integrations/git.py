from briefcase.exceptions import BriefcaseCommandError


def verify_git_is_installed():
    """
    Verify if git is installed.

    Unfortunately, `import git` triggers a call on the operating system
    to run the git executable. On some platforms (notably macOS), the git
    binary has been instrumented such that if git *isnt'* installed,
    running git triggers a prompt to install Xcode. However, that messes
    with the UX workflow.

    So - we defer importing git until we actually know we need it. This
    enables Briefcase to start us to do other Xcode checks as part of
    macOS workflows, and ensures that "briefcase --help" works on other
    platforms without raising an error.

    :returns: The git module, if `git` is installed and available.
    """
    # Check whether the git executable could be imported.
    try:
        import git
        return git
    except ImportError:
        raise BriefcaseCommandError("""
Briefcase requires git, but it is not installed (or is not on your PATH). Visit:

    https://git-scm.com/

to download and install git. If you have installed git recently and are still
getting this error, you may need to restart your terminal session.
""")
