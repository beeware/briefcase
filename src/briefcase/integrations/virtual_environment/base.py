from abc import ABC, abstractmethod
from pathlib import Path

from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT


class EnvManager(ABC):
    """Strategy class encapsulating the behavioural differences between an isolated
    Python virtual environment and a no-op (passthrough) environment.

    A :class:`VirtualEnvironment` instance delegates all mode-specific behaviour
    (creation, cleanup, argv rewriting, environment construction, executable
    resolution, wait-bar messaging) to its `EnvManager`. Concrete subclasses
    MUST implement every abstract member.

    This is an internal extension point. It is reachable only at
    `briefcase.integrations.virtual_environment.EnvManager` and is NOT
    re-exported from `briefcase.integrations.__init__`.
    """

    def __init__(self, tools: ToolCache, venv_path: Path):
        """Initialise the environment manager on a specific path.

        :param tools: The shared :class:`ToolCache` instance.
        :param venv_path: The on-disk path associated with this environment.
            For an isolated venv, this is the venv directory; for a no-op
            environment, it is the directory used for the marker file.
        """
        self.tools = tools
        self.venv_path = venv_path

    @property
    @abstractmethod
    def executable(self) -> Path:
        """The Python interpreter associated with this environment."""

    @property
    @abstractmethod
    def bin_dir(self) -> Path:
        """The directory containing the interpreter and its scripts."""

    @abstractmethod
    def exists(self) -> bool:
        """`True` iff the environment is in a usable state.

        For an isolated venv: the venv directory exists and contains
        `pyvenv.cfg`. For a no-op environment: always `True`.
        """

    @abstractmethod
    def prepare(self, recreate=False) -> bool:
        """Prepare a venv at the given environment.

        If the venv does not already exist, or a recreate has been requested, create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if venv creation or pip upgrade fails.
        """

    @abstractmethod
    def clean(self) -> None:
        """Remove the on-disk state associated with this environment."""

    @abstractmethod
    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Adjust subprocess arguments for execution in this environment."""

    @abstractmethod
    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str | None] | None:
        """Build the environment dict to pass to `subprocess`.

        :param overrides: A dictionary of environment keys to set, overriding the
            default environment.
        :returns: An updated environment applying modifications to enable the virtual
            environment
        """
