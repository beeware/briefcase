from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT, SubprocessArgT


class Docker(Tool):
    name = "docker"
    full_name = "Docker"

    WRONG_DOCKER_VERSION_ERROR = """\
Briefcase requires Docker 19 or higher, but you are currently running
version {docker_version}. Visit:

    {install_url}

to download and install an updated version of Docker.
"""
    UNKNOWN_DOCKER_VERSION_WARNING = """
*************************************************************************
** WARNING: Unable to determine the version of Docker                  **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you
    experience problems, this is almost certainly the cause of those
    problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

      docker --version

    from the command prompt.

*************************************************************************
"""
    DOCKER_INSTALLATION_STATUS_UNKNOWN_WARNING = """
*************************************************************************
** WARNING: Unable to determine if Docker is installed                 **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you
    experience problems, this is almost certainly the cause of those
    problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

      docker --version

    from the command prompt.

*************************************************************************
"""
    DOCKER_NOT_INSTALLED_ERROR = """\
Briefcase requires Docker, but it is not installed (or is not on your PATH).
Visit:

    {install_url}

to download and install Docker manually.

If you have installed Docker recently and are still getting this error, you may
need to restart your terminal session.
"""

    LACKS_PERMISSION_ERROR = """\
Docker has been installed, but Briefcase is unable to invoke
Docker commands. It is possible that your user does not have
permissions to invoke Docker.

See https://docs.docker.com/engine/install/linux-postinstall/
for details on configuring access to your Docker installation.
"""
    DAEMON_NOT_RUNNING_ERROR = """\
Briefcase is unable to use Docker commands. It appears the Docker
daemon is not running.

See https://docs.docker.com/config/daemon/ for details on how to
configure your Docker daemon.
"""
    GENERIC_DOCKER_ERROR = """\
Briefcase was unable to use Docker commands. Check your Docker
installation, and try again.
"""
    BUILDX_PLUGIN_MISSING = """\
Docker is installed and available for use but the buildx plugin
is not installed. Briefcase leverages the BuildKit Docker backend
to build Docker images and the buildx plugin makes this available.

See https://docs.docker.com/go/buildx/ to install the buildx plugin.
"""

    # Platform-specific template context dictionary for Docker installation details
    DOCKER_INSTALL_URL = {
        "Windows": "https://docs.docker.com/docker-for-windows/install/",
        "Darwin": "https://docs.docker.com/docker-for-mac/install/",
        "Linux": "https://docs.docker.com/engine/install/#server",
    }

    def __init__(self, tools: ToolCache, image_tag: str | None = None):
        """A wrapper for the user-installed Docker.

        :param tools: ToolCache of available tools
        :param image_tag: An optional image used to access attributes of the Docker
            environment, such as how user permissions are managed in bind mounts. A
            lightweight image will be used if one is not specified but this image is not
            at all bound to the instance.
        """
        super().__init__(tools=tools)
        self.is_user_mapped = self._is_user_mapping_enabled(image_tag)

    @classmethod
    def verify_install(
        cls,
        tools: ToolCache,
        image_tag: str | None = None,
        **kwargs,
    ) -> Docker:
        """Verify Docker is installed and operational.

        :param tools: ToolCache of available tools
        :param image_tag: An optional image used during verification to access
            attributes of the local Docker environment. This image is not bound to the
            instance and only used during instantiation.
        """
        # short circuit since already verified and available
        if hasattr(tools, "docker"):
            return tools.docker

        cls._version_compat(tools=tools)
        cls._user_access(tools=tools)
        cls._buildx_installed(tools=tools)

        tools.docker = Docker(tools=tools, image_tag=image_tag)
        return tools.docker

    @classmethod
    def _version_compat(cls, tools: ToolCache):
        """Verify Docker version is compatible."""
        try:
            # Try to get the version of docker that is installed.
            output = tools.subprocess.check_output(["docker", "--version"]).strip("\n")

            # Do a simple check that the docker that was invoked
            # actually looks like the real deal, and is a version that
            # meets our requirements.
            if output.startswith("Docker version "):
                docker_version = output[15:]
                version = docker_version.split(".")
                if int(version[0]) < 19:
                    # Docker version isn't compatible.
                    raise BriefcaseCommandError(
                        cls.WRONG_DOCKER_VERSION_ERROR.format(
                            docker_version=docker_version,
                            install_url=cls.DOCKER_INSTALL_URL[tools.host_os],
                        )
                    )

            else:
                tools.logger.warning(cls.UNKNOWN_DOCKER_VERSION_WARNING)
        except subprocess.CalledProcessError:
            tools.logger.warning(cls.DOCKER_INSTALLATION_STATUS_UNKNOWN_WARNING)
        except OSError as e:
            # Docker executable doesn't exist.
            raise BriefcaseCommandError(
                cls.DOCKER_NOT_INSTALLED_ERROR.format(
                    install_url=cls.DOCKER_INSTALL_URL[tools.host_os]
                )
            ) from e

    @classmethod
    def _user_access(cls, tools: ToolCache):
        """Verify Docker is operational for user."""
        try:
            # Invoke a docker command to check if the daemon is running,
            # and the user has sufficient permissions.
            # We don't care about the output, just that it succeeds.
            tools.subprocess.check_output(["docker", "info"])
        except subprocess.CalledProcessError as e:
            failure_output = e.output
            if "permission denied while trying to connect" in failure_output:
                raise BriefcaseCommandError(cls.LACKS_PERMISSION_ERROR) from e
            elif (
                # error message on Ubuntu
                "Is the docker daemon running?" in failure_output
                # error message on macOS
                or "connect: connection refused" in failure_output
            ):
                raise BriefcaseCommandError(cls.DAEMON_NOT_RUNNING_ERROR) from e
            else:
                raise BriefcaseCommandError(cls.GENERIC_DOCKER_ERROR) from e

    @classmethod
    def _buildx_installed(cls, tools: ToolCache):
        """Verify the buildx plugin is installed."""
        try:
            tools.subprocess.check_output(["docker", "buildx", "version"])
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(cls.BUILDX_PLUGIN_MISSING)

    def _write_test_path(self) -> Path:
        """Host system filepath to perform write test from a container."""
        return Path.cwd() / "build" / "container_write_test"

    def _is_user_mapping_enabled(self, image_tag: str | None = None) -> bool:
        """Determine whether Docker is mapping users between the container and the host.

        Docker can be installed in different ways on Linux that significantly impact how
        containers interact with the host system. Of particular note is ownership of
        files and directories in bind mounts (i.e. mounts using --volume).

        Traditionally, Docker would pass through the UID/GID of the user used inside a
        container as the owner of files created within the bind mount. And since the
        default user inside containers is root, the files would be owned by root on the
        host file system; this prevents later interaction with those files by the host.
        To work around this, the Dockerfile can use a step-down user with a UID and GID
        that matches the host user running Docker.

        Other installation methods of Docker, though, are not compatible with using such
        a step-down user. This includes Docker Desktop and rootless Docker (although,
        even a traditional installation of Docker Engine can be configured similarly).
        In these modes, Docker maps the host user to the root user inside the container;
        this mapping is transparent and would require changes to the host environment to
        disable, if it can be disabled at all. This allows files created in bind mounts
        inside the container to be owned on the host file system by the user running
        Docker. Additionally, though, because the host user is mapped to root inside the
        container, any files that were created by the host user in the bind mount
        outside the container are owned by root inside the container; therefore, a step-
        down user could not interact with such bind mount files inside the container.

        To accommodate these different modes, this checks which user owns a file that is
        created inside a bind mount in the container. If the owning user of that file on
        the host file system is root, then a step-down user is necessary inside
        containers. If the owning user is the host user, root should be used.

        On macOS, Docker Desktop is the only option to use Docker and user mapping
        happens differently such that any user in the container is mapped to the host
        user. Instead of leveraging user namespaces as on Linux, this user mapping
        manifests as a consequence of bind mounts being implemented as NFS shares
        between macOS and the Linux VM that Docker Desktop runs containers in. So,
        using a step-down user on macOS is effectively inconsequential.

        On Windows WSL 2, Docker Desktop operates similarly to how it does on Linux.
        However, user namespace mapping is not possible because the Docker Desktop VM
        and the WSL distro are already running in different user namespaces...and
        therefore, Docker cannot even see the users in the distro to map them in to the
        container. So, a step-down user is always used.

        ref: https://docs.docker.com/engine/security/userns-remap/

        :param image_tag: The image:tag to use to create the container for the test; if
            one is not specified, then `alpine:latest` will be used.
        :returns: True if users are being mapped; False otherwise
        """
        host_write_test_path = self._write_test_path()
        container_write_test_path = PurePosixPath(
            "/host_write_test", host_write_test_path.name
        )

        image_tag = "alpine" if image_tag is None else image_tag
        # Cache the image first so the attempts below to run the image don't
        # log irrelevant errors when the image may just have a simple typo
        self.cache_image(image_tag)

        docker_run_cmd = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{host_write_test_path.parent}:{container_write_test_path.parent}:z",
            image_tag,
        ]

        host_write_test_path.parent.mkdir(exist_ok=True)

        try:
            host_write_test_path.unlink(missing_ok=True)
        except OSError as e:
            raise BriefcaseCommandError(
                f"""\
The file path used to determine how Docker is mapping users between the host
and Docker containers already exists and cannot be automatically deleted.

    {host_write_test_path}

Delete this file and run Briefcase again.
"""
            ) from e

        try:
            self.tools.subprocess.run(
                docker_run_cmd + ["touch", container_write_test_path],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Unable to determine if Docker is mapping users"
            ) from e

        # if the file is not owned by `root`, then Docker is mapping usernames
        is_user_mapped = 0 != self.tools.os.stat(host_write_test_path).st_uid

        try:
            self.tools.subprocess.run(
                docker_run_cmd + ["rm", "-f", container_write_test_path],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Unable to clean up from determining if Docker is mapping users"
            ) from e

        return is_user_mapped

    def cache_image(self, image_tag: str):
        """Ensures an image is available and cached locally.

        While many Docker commands for an image will pull that image in-line with the
        command if it isn't already cached, this pollutes the console output with
        details about pulling the image. This can be particularly troublesome when the
        output from a command run inside a container using the image is desired.

        Note: This will not update an already cached image if a newer version is
        available in the registry.

        :param image_tag: Image name/tag to pull if not locally cached
        """
        image_id = self.tools.subprocess.check_output(
            ["docker", "images", "-q", image_tag]
        ).strip()

        if not image_id:
            self.tools.logger.info(
                f"Downloading Docker base image for {image_tag}...",
                prefix="Docker",
            )
            try:
                # disable streaming so image download progress bar is shown
                self.tools.subprocess.run(
                    ["docker", "pull", image_tag],
                    check=True,
                    stream_output=False,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to obtain the Docker image for {image_tag}. "
                    "Is the image name correct?"
                ) from e

    def check_output(self, args: list[SubprocessArgT], image_tag: str) -> str:
        """Run a process inside a Docker container, capturing output.

        This ensures the image is locally cached and then runs a bare Docker invocation;
        it's really only useful for running simple commands on an image, ensuring that
        the container is destroyed afterward. In most cases, you'll want to use an app
        context, rather than this.

        :param args: The list of arguments to pass to the Docker instance.
        :param image_tag: The Docker image to run
        """
        self.cache_image(image_tag)

        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            ["docker", "run", "--rm", image_tag] + args
        )


class DockerAppContext(Tool):
    name = "docker_app_context"
    full_name = "Docker"

    def __init__(self, tools: ToolCache, app: AppConfig):
        super().__init__(tools=tools)
        self.app: AppConfig = app
        self.app_base_path: Path
        self.host_bundle_path: Path
        self.host_data_path: Path
        self.image_tag: str
        self.python_version: str

    @property
    def docker_briefcase_path(self) -> PurePosixPath:
        """The briefcase data directory used inside container."""
        return PurePosixPath("/briefcase")

    @classmethod
    def verify_install(
        cls,
        tools: ToolCache,
        app: AppConfig,
        image_tag: str,
        dockerfile_path: Path,
        app_base_path: Path,
        host_bundle_path: Path,
        host_data_path: Path,
        python_version: str,
        **kwargs,
    ) -> DockerAppContext:
        """Verify that docker is available as an app-bound tool.

        Creates or updates the Docker image for the app to run commands in a context for
        the App.

        :param tools: ToolCache of available tools
        :param app: Current Appconfig
        :param image_tag: Tag to assign to Docker image
        :param dockerfile_path: Dockerfile to use to build Docker image
        :param app_base_path: Base directory path for App
        :param host_bundle_path: Base directory for where App is built
        :param host_data_path: Base directory for host's Briefcase data
        :param python_version: Version of python, e.g. 3.10
        :returns: A wrapper for a Docker app context.
        """
        # short circuit since already verified and available
        if hasattr(tools[app], "app_context"):
            return tools[app].app_context

        Docker.verify(tools=tools)

        tools[app].app_context = DockerAppContext(tools=tools, app=app)
        tools[app].app_context.prepare(
            image_tag=image_tag,
            dockerfile_path=dockerfile_path,
            app_base_path=app_base_path,
            host_bundle_path=host_bundle_path,
            host_data_path=host_data_path,
            python_version=python_version,
        )
        return tools[app].app_context

    def prepare(
        self,
        image_tag: str,
        dockerfile_path: Path,
        app_base_path: Path,
        host_bundle_path: Path,
        host_data_path: Path,
        python_version: str,
    ):
        """Create/update the Docker image from the app's Dockerfile."""
        self.app_base_path = app_base_path
        self.host_bundle_path = host_bundle_path
        self.host_data_path = host_data_path
        self.image_tag = image_tag
        self.python_version = python_version

        self.tools.logger.info(
            "Building Docker container image...",
            prefix=self.app.app_name,
        )
        with self.tools.input.wait_bar("Building Docker image..."):
            with self.tools.logger.context("Docker"):
                try:
                    self.tools.subprocess.run(
                        [
                            "docker",
                            "build",
                            "--progress",
                            "plain",
                            "--tag",
                            self.image_tag,
                            "--file",
                            dockerfile_path,
                            "--build-arg",
                            f"SYSTEM_REQUIRES={' '.join(getattr(self.app, 'system_requires', ''))}",
                            "--build-arg",
                            f"HOST_UID={self.tools.os.getuid()}",
                            "--build-arg",
                            f"HOST_GID={self.tools.os.getgid()}",
                            Path(
                                self.app_base_path,
                                *self.app.sources[0].split("/")[:-1],
                            ),
                        ],
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    raise BriefcaseCommandError(
                        f"Error building Docker container image for {self.app.app_name}."
                    ) from e

    def _dockerize_path(self, arg: str) -> str:  # pragma: no-cover-if-is-windows
        """Relocate any local path into the equivalent location on the docker
        filesystem.

        Converts:
        * any reference to `sys.executable` into the python executable in the docker container
        * any path in <build path> into the equivalent stemming from /app
        * any path in <data path> into the equivalent in ~/.cache/briefcase

        :param arg: The string argument to convert to dockerized paths
        :returns: A string where all convertible paths have been replaced.
        """
        if arg == sys.executable:
            return f"python{self.python_version}"
        arg = arg.replace(os.fsdecode(self.host_bundle_path), "/app")
        arg = arg.replace(
            os.fsdecode(self.host_data_path), os.fsdecode(self.docker_briefcase_path)
        )

        return arg

    def _dockerize_args(
        self,
        args: SubprocessArgsT,
        interactive: bool = False,
        mounts: list[tuple[str | Path, str | Path]] | None = None,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> list[str]:  # pragma: no-cover-if-is-windows
        """Convert arguments and environment into a Docker-compatible form. Convert an
        argument and environment specification into a form that can be used as arguments
        to invoke Docker. This involves:

         * Configuring the Docker invocation to reference the
           appropriate container image, and clean up afterward
         * Setting volume mounts for the container instance
         * Transforming any references to local paths into Docker path references.

        :param args: The arguments for the command to be invoked
        :param env: The environment specification for the command to be executed
        :param cwd: The working directory for the command to be executed
        :returns: A list of arguments that can be used to invoke the command
            inside a docker container.
        """
        docker_args = ["docker", "run", "--rm"]

        # Add "-it" if in interactive mode
        if interactive:
            docker_args.append("-it")

        # Add default volume mounts for the app folder, plus the Briefcase data
        # path.
        #
        # The :z suffix on volume mounts allows SELinux to modify the host
        # mount; it is ignored on non-SELinux platforms.
        docker_args.extend(
            [
                "--volume",
                f"{self.host_bundle_path}:/app:z",
                "--volume",
                f"{self.host_data_path}:{self.docker_briefcase_path}:z",
            ]
        )

        # Add any extra volume mounts
        if mounts:
            for source, target in mounts:
                docker_args.extend(["--volume", f"{source}:{target}:z"])

        # If any environment variables have been defined, pass them in
        # as --env arguments to Docker.
        if env:
            for key, value in env.items():
                docker_args.extend(["--env", f"{key}={self._dockerize_path(value)}"])

        # If a working directory has been specified, pass it
        if cwd:
            docker_args.extend(["--workdir", self._dockerize_path(os.fsdecode(cwd))])

        # ... then the image name to create the temporary container with
        docker_args.append(self.image_tag)

        # ... then add the command (and its arguments) to run in the container
        docker_args.extend([self._dockerize_path(str(arg)) for arg in args])

        return docker_args

    def run(
        self,
        args: SubprocessArgsT,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        interactive: bool = False,
        mounts: list[tuple[str | Path, str | Path]] | None = None,
        **kwargs,
    ):
        """Run a process inside a Docker container."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.run()" behaves as closely to
        # "subprocess.run()" as possible.
        with self.tools.logger.context("Docker"):
            if interactive:
                kwargs["stream_output"] = False

            self.tools.subprocess.run(
                self._dockerize_args(
                    args,
                    interactive=interactive,
                    mounts=mounts,
                    env=env,
                    cwd=cwd,
                ),
                **kwargs,
            )

    def check_output(
        self,
        args: SubprocessArgsT,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        mounts: list[tuple[str | Path, str | Path]] | None = None,
        **kwargs,
    ) -> str:
        """Run a process inside a Docker container, capturing output."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            self._dockerize_args(args, mounts=mounts, env=env, cwd=cwd),
            **kwargs,
        )
