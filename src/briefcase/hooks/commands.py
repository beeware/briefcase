from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from briefcase.exceptions import BriefcaseCommandError
from briefcase.hooks.base import BaseHook

if TYPE_CHECKING:
    from briefcase.config import FinalizedAppConfig
    from briefcase.hooks.base import HookCommandAPI


class CommandsHook(BaseHook):
    """Runs the commands an app configures in its ``hooks`` table.

    Each command is a list of arguments, run without a shell from the project
    directory, with the environment extended by ``BRIEFCASE_APP_NAME``,
    ``BRIEFCASE_BUNDLE_PATH``, ``BRIEFCASE_HOOK_STAGE``, ``BRIEFCASE_OUTPUT_FORMAT``
    and ``BRIEFCASE_PLATFORM``.
    """

    @property
    def name(self) -> str:
        return "commands"

    def invoke(
        self,
        stage: str,
        app: FinalizedAppConfig,
        command: HookCommandAPI,
        **options,
    ) -> None:
        for args in app.hooks.get(stage, []):
            cmdline = " ".join(args)
            command.console.info(
                f"Running {stage} hook command: {cmdline}",
                prefix=app.app_name,
            )
            try:
                command.tools.subprocess.run(
                    args,
                    check=True,
                    cwd=command.base_path,
                    env={
                        "BRIEFCASE_APP_NAME": app.app_name,
                        "BRIEFCASE_BUNDLE_PATH": str(command.bundle_path(app)),
                        "BRIEFCASE_HOOK_STAGE": stage,
                        "BRIEFCASE_OUTPUT_FORMAT": command.output_format,
                        "BRIEFCASE_PLATFORM": command.platform,
                    },
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"The {stage} hook command {cmdline!r} for {app.app_name!r} "
                    f"failed (exit code {e.returncode})."
                ) from e
            except OSError as e:
                raise BriefcaseCommandError(
                    f"The {stage} hook command {cmdline!r} for {app.app_name!r} "
                    f"could not be run: {e}"
                ) from e
