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

    def __getitem__(
        self,
        env_manager: EnvManagerT | None = "venv",
    ) -> type[VirtualEnvironment]:
        """Verify and return the requested `VirtualEnvironment` class.

        The environment type will be verified; if the tools to support the environment
        are not available, an error will be raised.

        :param env_manager: The environment manager type to return
        :returns: A subclass of VirtualEnvironment
        """
        EnvManagerClass = {
            None: NoOpVirtualEnvironment,
            "uv": UvVirtualEnvironment,
            "venv": VenvVirtualEnvironment,
            "conda": CondaVirtualEnvironment,
            "pixi": PixiVirtualEnvironment,
        }[env_manager]

        # Verify that the environment manager is available.
        EnvManagerClass.verify(self.tools)

        return EnvManagerClass
