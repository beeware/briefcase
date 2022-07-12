from briefcase.exceptions import MissingToolError


class VisualStudio:
    name = "visualstudio"

    def __init__(self, command):
        self.command = command

    @property
    def msbuild_path(self):
        # FIXME: This shouldn't be hard coded
        return "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe"

    @classmethod
    def verify(cls, command):
        """Verify that Visual Studio is available.

        :param command: The command that needs to use Visual Studio
        :param install: Should the tool be installed if it is not found?
        :returns: A valid Visual Studio tool wrapper. If Visual Studio is not
            available, raises MissingToolError.
        """
        visualstudio = VisualStudio(command)

        # FIXME: Put a better implementation here.
        if not visualstudio.exists():
            raise MissingToolError("RCEdit")

        return visualstudio

    @property
    def managed_install(self):
        return False

    def exists(self):
        # FIXME: Acutally verify existence
        return True
