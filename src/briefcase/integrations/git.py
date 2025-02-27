from __future__ import annotations

from types import ModuleType

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache


class Git(Tool):
    name = "git"
    full_name = "Git"

    MIN_VERSION = (2, 17, 0)
    GIT_URL = "https://git-scm.com/"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> ModuleType:
        """Verify if git is installed.

        Unfortunately, `import git` triggers a call on the operating system
        to run the git executable. On some platforms (notably macOS), the git
        binary has been instrumented such that if git *isn't* installed,
        running git triggers a prompt to install Xcode. However, that messes
        with the UX workflow.

        So - we defer importing git until we actually know we need it. This
        enables Briefcase to start to do other Xcode checks as part of the macOS
        workflows, and ensures that "briefcase --help" works on other platforms
        without raising an error.

        :param tools: ToolCache of available tools
        :returns: The git module, if `git` is installed and available.
        """
        # short circuit since already verified and available
        if hasattr(tools, "git"):
            return tools.git

        # Check whether the git executable could be imported.
        try:
            import git
        except ImportError as e:  # pragma: no cover
            # macOS provides git as part of the Xcode command line tools,
            # and also hijacks /usr/bin/git with a trigger that prompts the
            # installation of those tools. Customize the message to account
            # for this.
            if tools.host_os == "Darwin":
                raise BriefcaseCommandError(
                    f"""\
Briefcase requires git, but it is not installed. Xcode provides git; you should
be shown a dialog prompting you to install Xcode and the Command Line Developer
Tools. Select "Install" to install the Command Line Developer Tools.

Alternatively, you can visit:

    {cls.GIT_URL}

to download and install git manually.

If you have installed git recently and are still getting this error, you may
need to restart your terminal session.
"""
                ) from e

            else:
                raise BriefcaseCommandError(
                    f"""\
Briefcase requires git, but it is not installed (or is not on your PATH). Visit:

    {cls.GIT_URL}

to download and install git manually.

If you have installed git recently and are still getting this error, you may
need to restart your terminal session.
"""
                ) from e

        installed_version = git.cmd.Git().version_info
        if installed_version < cls.MIN_VERSION:
            raise BriefcaseCommandError(
                f"At least Git v{'.'.join(map(str, cls.MIN_VERSION))} is required; "
                f"however, v{'.'.join(map(str, installed_version))} is installed.\n"
                "\n"
                f"Please update Git; downloads are available at {cls.GIT_URL}.",
                skip_logfile=True,
            )

        tools.console.configure_stdlib_logging("git")

        tools.git = git
        return git
