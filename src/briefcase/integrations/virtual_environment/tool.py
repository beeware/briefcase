from pathlib import Path

from briefcase.config import EnvManagerT
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.virtual_environment.base import VirtualEnvironment
from briefcase.integrations.virtual_environment.conda import CondaVirtualEnvironment
from briefcase.integrations.virtual_environment.noop import NoOpVirtualEnvironment
from briefcase.integrations.virtual_environment.pixi import PixiVirtualEnvironment
from briefcase.integrations.virtual_environment.std_venv import VenvVirtualEnvironment
from briefcase.integrations.virtual_environment.uv import UvVirtualEnvironment


class VirtualEnvironmentManager(Tool):
    name = "virtual_environment"
    full_name = "Virtual Environment manager"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> "VirtualEnvironmentManager":
        """Make virtual environment management available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "virtual_environment"):
            return tools.virtual_environment

        tools.virtual_environment = VirtualEnvironmentManager(tools=tools)
        return tools.virtual_environment

    def __call__(
        self,
        venv_path: Path,
        *,
        isolated: bool = True,
        platform: str | None = None,
        arch: str | None = None,
        env_manager: EnvManagerT = "venv",
    ) -> VirtualEnvironment:
        """Construct and return a `VirtualEnvironment` for the requested mode.

        The constructor of the returned object performs the lifecycle work
        synchronously: by the time this method returns, the venv exists on
        disk (in isolated mode) or the no-op marker has been checked/written
        (in passthrough mode), and the returned object's `created` flag
        reflects whether this invocation produced freshly initialised state.

        :param venv_path: Filesystem path associated with the environment. For
            an isolated venv this is the venv directory; for a no-op
            environment it is the directory used for the marker file.
        :param isolated: If `True` (the default), use `VenvVirtualEnvironment`
            (a real, dedicated venv created via `python -m venv`). If
            `False`, use `NoOpVirtualEnvironment` (passthrough to the ambient
            interpreter, with first-use detection via a marker file).
        :returns: A instance of a Virtual Environment.
        :raises BriefcaseCommandError: if the environment cannot be created or
            initialised.
        """
        if not isolated:
            env_manager = None

        venv: VirtualEnvironment = {
            None: NoOpVirtualEnvironment,
            "uv": UvVirtualEnvironment,
            "conda": CondaVirtualEnvironment,
            "pixi": PixiVirtualEnvironment,
        }.get(env_manager, VenvVirtualEnvironment)(
            self.tools,
            venv_path,
            platform=platform,
            arch=arch,
        )

        return venv
