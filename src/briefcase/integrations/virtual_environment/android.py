from briefcase.integrations.virtual_environment.noop import NoOpVirtualEnvironment


class LegacyAndroidVirtualEnvironment(NoOpVirtualEnvironment):
    """Install wheels for Android Python versions unsupported by xbuild.

    No target interpreter is needed: pip runs in Briefcase's environment with
    Android wheel tags and environment markers.
    """

    @property
    def pip_args(self):
        return [
            "-m",
            "briefcase.integrations.virtual_environment.android_pip",
            self.arch,
        ]
