import subprocess as stdlib_subprocess
from pathlib import Path

from briefcase.integrations import subprocess
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import EnvManager
from briefcase.integrations.virtual_environment.noop import NoOpEnvManager
from briefcase.integrations.virtual_environment.std_venv import VenvEnvManager


class VirtualEnvironment:
    """A managed Python environment.

    The virtual environment will exist on disk after an instance of this
    object has been construted. The environment becomes active when used
    as a context manager.

    All behaviour specifics (creation, cleanup, argv rewriting, environment
    construction, executable resolution, wait-bar messaging) is delegated to
    the configured `EnvManager`.
    """

    def __init__(
        self,
        tools: ToolCache,
        manager: EnvManager,
        *,
        recreate: bool = False,
    ):
        """Initialise the environment, performing any required lifecycle work.

        :param tools: The shared :class:`ToolCache`.
        :param manager: The :class:`EnvManager` instance encapsulating the
            mode-specific behaviour.
        :param recreate: If `True`, the environment is cleaned and
            re-initialised, even if it already exists on disk.
        :raises BriefcaseCommandError: if the environment cannot be created or
            initialised (e.g., `python -m venv` fails, or the pip-upgrade
            step inside the new venv fails).
        """
        self.tools = tools
        self.manager = manager
        self.created = manager.prepare(recreate=recreate)

    def exists(self) -> bool:
        """Determine if the environment is in a usable state."""
        return self.manager.exists()

    def clean(self) -> bool:
        """Clean up the virtual environment."""
        return self.manager.clean()

    # -- Subprocess routing -------------------------------------------------

    def run(self, args: SubprocessArgsT, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the virtual environment.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to `subprocess.run`.
        :returns: `CompletedProcess` from the subprocess execution.
        """
        args = self.manager.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.manager.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: SubprocessArgsT, **kwargs) -> stdlib_subprocess.Popen:
        """Create a Popen instance for a command in the virtual environment.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to `subprocess.Popen`.
        :returns: A `Popen` instance for the subprocess execution.
        """
        args = self.manager.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.manager.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.Popen(args, **kwargs)

    def check_output(self, args: SubprocessArgsT, **kwargs) -> str:
        """Run a command in the virtual environment, return process output.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to
            `subprocess.check_output`.
        :returns: String output from the subprocess execution.
        """
        args = self.manager.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.manager.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.check_output(args, **kwargs)

    # -- Context-manager protocol -------------------------------------------

    def __enter__(self) -> "VirtualEnvironment":
        """Return `self`.

        The lifecycle work was performed in `__init__`.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class VirtualEnvironmentTool(Tool):
    name = "virtual_environment"
    full_name = "Virtual Environment management"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> "VirtualEnvironmentTool":
        """Make virtual environment available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "virtual_environment"):
            return tools.virtual_environment

        tools.virtual_environment = VirtualEnvironmentTool(tools=tools)
        return tools.virtual_environment

    def create(
        self,
        venv_path: Path,
        *,
        isolated: bool = True,
        recreate: bool = False,
    ) -> VirtualEnvironment:
        """Construct and return a :class:`VirtualEnvironment` for the requested mode.

        The constructor of the returned object performs the lifecycle work
        synchronously: by the time this method returns, the venv exists on
        disk (in isolated mode) or the no-op marker has been checked/written
        (in passthrough mode), and the returned object's `created` flag
        reflects whether this invocation produced freshly initialised state.

        :param venv_path: Filesystem path associated with the environment. For
            an isolated venv this is the venv directory; for a no-op
            environment it is the directory used for the marker file.
        :param isolated: If `True` (the default), use `VenvEnvManager`
            (a real, dedicated venv created via `python -m venv`). If
            `False`, use `NoOpEnvManager` (passthrough to the ambient
            interpreter, with first-use detection via a marker file).
        :param recreate: If `True`, clean and re-initialise the environment,
            even if it already exists.
        :returns: A fully-prepared :class:`VirtualEnvironment`. Use it as a
            context manager (`with env as venv:`) for scoping; `__enter__`
            returns `self` and has no side effects.
        :raises BriefcaseCommandError: if the environment cannot be created or
            initialised.
        """
        if isolated:
            manager: EnvManager = VenvEnvManager(self.tools, venv_path)
        else:
            manager = NoOpEnvManager(self.tools, venv_path)

        return VirtualEnvironment(self.tools, manager, recreate=recreate)
