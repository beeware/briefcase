from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from briefcase.config import FinalizedAppConfig
    from briefcase.console import Console
    from briefcase.integrations.base import ToolCache

# The stages at which hook plugins are invoked, in command order. Each command
# invokes its `pre_` stage before, and its `post_` stage after, its own work.
HOOK_STAGES = (
    "pre_create",
    "post_create",
    "pre_update",
    "post_update",
    "pre_build",
    "post_build",
    "pre_run",
    "post_run",
    "pre_package",
    "post_package",
    "pre_publish",
    "post_publish",
    "pre_dev",
    "post_dev",
)


@runtime_checkable
class HookCommandAPI(Protocol):
    """Stable API surface exposed to hook plugins.

    This defines the minimal set of attributes and methods that a plugin can rely on
    from the ``command`` parameter passed to a hook stage.
    """

    console: Console
    tools: ToolCache
    base_path: Path
    platform: str
    output_format: str
    command: str

    def bundle_path(self, app: FinalizedAppConfig) -> Path: ...

    def build_path(self, app: FinalizedAppConfig) -> Path: ...


class BaseHook(ABC):
    """Definition for a plugin that adds steps to Briefcase commands.

    Override the stage methods the plugin needs; each does nothing by default. A
    plugin that handles every stage the same way can override ``invoke()`` instead.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The human-readable name of the hook."""

    def invoke(
        self,
        stage: str,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Run the hook for a stage.

        :param stage: The stage being run; one of ``HOOK_STAGES``.
        :param app: The application the command is operating on.
        :param command: The command invoking the hook.
        :param options: The options the command received for the app.
        """
        getattr(self, stage)(app, command, **options)

    # Deliberately empty: a plugin overrides only the stages it needs.
    def pre_create(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app's template is generated."""

    def post_create(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has been created."""

    def pre_update(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app's code is updated."""

    def post_update(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has been updated."""

    def pre_build(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app is built."""

    def post_build(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has been built."""

    def pre_run(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app is started."""

    def post_run(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has exited."""

    def pre_package(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app is packaged."""

    def post_package(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has been packaged."""

    def pre_publish(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app is published."""

    def post_publish(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has been published."""

    def pre_dev(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs before the app is started in the dev environment."""

    def post_dev(  # noqa: B027
        self,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        """Runs after the app has exited the dev environment."""
