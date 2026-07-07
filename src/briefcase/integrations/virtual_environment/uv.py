import os
import shutil
import subprocess as subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class UvVirtualEnvironment(VirtualEnvironment):
    """An environment manager using uv."""

    def exists(self) -> bool:
        """`True` iff the uv environment directory and its `pyvenv.cfg` are present."""
        return self.venv_path.exists() and (self.venv_path / "pyvenv.cfg").exists()

    def prepare(self, recreate=False) -> bool:
        """Prepare a uv venv at the given environment.

        If the venv does not already exist, or a recreate has been requested, create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if venv creation or pip upgrade fails.
        """
        creating = "Creating"
        if self.exists():
            if recreate:
                creating = "Recreating"
            else:
                return False

        with self.tools.console.wait_bar(
            f"{creating} uv environment ({self.venv_path.name})..."
        ):
            if recreate:
                self.clean()

            try:
                self.venv_path.parent.mkdir(parents=True, exist_ok=True)
                self.tools.subprocess.run(
                    [
                        "uv",
                        "venv",
                        "--python",
                        sys.executable,
                        "--seed",
                        self.venv_path,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Failed to create uv environment at {self.venv_path}"
                ) from e

        return True

    def clean(self) -> None:
        """Remove the venv directory tree if it exists."""
        if self.exists():
            shutil.rmtree(self.venv_path)

    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Replace the head argument with the venv's Python iff it equals
        `sys.executable` (case-insensitive, normalised).

        Empty inputs are returned unchanged. Otherwise a fresh `list` is
        returned; the input is never mutated.
        """
        if not args:
            return args
        head = os.fspath(args[0])
        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return ["uv", "run", "python", *args[1:]]
        return list(args)

    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str]:
        """Build a subprocess environment that activates the venv.

        Prepends the venv's `bin_dir` to `PATH`, sets `VIRTUAL_ENV`,
        and removes `PYTHONHOME`. Caller-supplied overrides are honoured.

        :param overrides: Caller-supplied environment overrides.
        :returns: An updated environment applying modifications
            to enable the virtual environment
        """
        env = dict(overrides) if overrides else {}

        old_path = env.get("PATH") or os.environ.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["VIRTUAL_ENV"] = os.fspath(self.venv_path)
        env.pop("PYTHONHOME", None)

        return env

    @property
    def platform_tag(self):
        """Output a uv python-platform tag.

        UV ignores the min_os_version; and uses GNU-style references to ARM64
        """
        platform = self.platform
        if platform is None:
            platform = {
                "Darwin": "macOS",
                "Windows": "windows",
            }.get(self.tools.host_os)

        arch = self.arch or self.tools.platform.machine()
        if arch.lower() == "arm64":
            arch = "aarch64"

        if platform == "macOS":
            return f"{arch}-apple-darwin"
        elif platform == "windows":
            return f"{arch}-pc-windows-msvc"
        else:
            raise NotImplementedError()

    def install_requirements(
        self,
        requires: list[str],
        allow_editable: bool = False,
        require_binary: bool = False,
        include_deps: bool = True,
        install_path: Path | None = None,
        min_os_version: str | None = None,
        extra_installer_args: list[str] | None = None,
        install_hint: str = "",
    ):
        """Install requirements into the environment with `uv pip`.

        :param requires: The list of requirements to install.
        :param allow_editable: Should editable installs be allowed?
        :param require_binary: Should binary wheels be required?
        :param include_deps: Should transitive dependencies be installed?
        :param install_path: Where should the packages be installed?
        :param min_os_version: The minimum OS version to enforce on packages.
        :param extra_installer_args: A list of additional arguments to pass to the
            installer.
        :param install_hint: If an install fails, an additional context-specific hint
            that can be displayed to the user.
        """
        uv_deps = []
        has_source_deps = False
        for req in requires:
            # Any requirement that is a local path, but *not* a reference to an archive
            # file (zip, tgz, etc) or wheel can be installed editable. If in doubt,
            # install non-editable.
            if (
                self.tools.file.is_local_path(req)
                and not self.tools.file.is_archive(req)
                and Path(req).suffix != ".whl"
            ):
                has_source_deps = True
                if allow_editable:
                    uv_deps.extend(["-e", req])
                else:
                    uv_deps.append(req)
            else:
                uv_deps.append(req)

        try:
            env = None
            install_args = []
            if install_path:
                install_args.append(f"--target={install_path}")

                if self.platform_tag:
                    install_args.extend(["--python-platform", self.platform_tag])
                    if min_os_version and self.platform == "darwin":
                        env = {"MACOSX_DEPLOYMENT_TARGET": min_os_version}

            if require_binary and not has_source_deps:
                # uv can't install a local directory if `--only-binary` is specified.
                # --only-binary is *required* for normal pip when --platform is used;
                # but it's not required for uv when using `--python-platform`.
                install_args.extend(["--only-binary", ":all:"])

            if not include_deps:
                install_args.append("--no-deps")

            if extra_installer_args:
                install_args.extend(extra_installer_args)

            self.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--upgrade",
                    *(["-vv"] if self.tools.console.is_deep_debug else []),
                    *install_args,
                    *uv_deps,
                ],
                check=True,
                encoding="UTF-8",
                env=env,
            )
        except subprocess.CalledProcessError as e:
            raise RequirementsInstallError(install_hint=install_hint) from e
