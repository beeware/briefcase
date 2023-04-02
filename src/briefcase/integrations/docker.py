import os
import subprocess
import sys
from pathlib import Path

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache


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

    def __init__(self, tools: ToolCache):
        self.tools = tools

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify Docker is installed and operational."""
        # short circuit since already verified and available
        if hasattr(tools, "docker"):
            return tools.docker

        cls._version_compat(tools=tools)
        cls._user_access(tools=tools)
        cls._buildx_installed(tools=tools)

        tools.docker = Docker(tools=tools)
        return tools.docker

    @classmethod
    def _version_compat(cls, tools):
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
    def _user_access(cls, tools):
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
    def _buildx_installed(cls, tools):
        """Verify the buildx plugin is installed."""
        try:
            tools.subprocess.check_output(["docker", "buildx", "version"])
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(cls.BUILDX_PLUGIN_MISSING)

    def check_output(self, args, image_tag):
        """Run a process inside a Docker container, capturing output.

        This is a bare Docker invocation; it's really only useful for running
        simple commands on an image, ensuring that the container is destroyed
        afterwards. In most cases, you'll want to use an app context, rather
        than this.

        :param args: The list of arguments to pass to the Docker instance.
        :param image_tag: The Docker image to run
        """
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            [
                "docker",
                "run",
                "--rm",
                image_tag,
            ]
            + args,
        )

    def prepare(self, image_tag):
        """Ensure that the given image exists, and is cached locally.

        This is achieved by trying to run a no-op command (echo) on the image;
        if it succeeds, the image exists locally.

        A pull is forced, so you can be certain that the image is up to date.

        :param image_tag: The Docker image to prepare
        """
        try:
            self.tools.subprocess.run(
                ["docker", "run", "--rm", image_tag, "printf", ""],
                check=True,
                stream_output=False,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to obtain the Docker base image {image_tag}. "
                "Is the image name correct?"
            ) from e


class DockerAppContext(Tool):
    def __init__(self, tools: ToolCache, app: AppConfig):
        self.tools = tools
        self.app = app

        self.app_base_path = None
        self.host_bundle_path = None
        self.host_data_path = None
        self.image_tag = None
        self.python_version = None

    @property
    def docker_data_path(self):
        """The briefcase data directory used inside container."""
        return "/home/brutus/.cache/briefcase"

    @classmethod
    def verify(
        cls,
        tools: ToolCache,
        app: AppConfig,
        image_tag: str,
        dockerfile_path: Path,
        app_base_path: Path,
        host_bundle_path: Path,
        host_data_path: Path,
        python_version: str,
    ):
        """Verify that docker is available as an app-bound tool.

        Creates or updates the Docker image for the app to run
        commands in a context for the App.

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

        tools[app].app_context = DockerAppContext(tools, app)
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

    def _dockerize_path(self, arg: str):
        """Relocate any local path into the equivalent location on the docker
        filesystem.

        Converts:
        * any reference to sys.executable into the python executable in the docker container
        * any path in <build path> into the equivalent stemming from /app
        * any path in <data path> into the equivalent in ~/.cache/briefcase

        :param arg: The string argument to convert to dockerized paths
        :returns: A string where all convertible paths have been replaced.
        """
        if arg == sys.executable:
            return f"python{self.python_version}"
        arg = arg.replace(os.fsdecode(self.host_bundle_path), "/app")
        arg = arg.replace(os.fsdecode(self.host_data_path), self.docker_data_path)

        return arg

    def _dockerize_args(self, args, interactive=False, mounts=None, env=None, cwd=None):
        """Convert arguments and environment into a Docker-compatible form. Convert an
        argument and environment specification into a form that can be used as arguments
        to invoke Docker. This involves:

         * Configuring the Docker invocation to reference the
           appropriate container image, and clean up afterwards
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
                f"{self.host_data_path}:{self.docker_data_path}:z",
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

    def run(self, args, env=None, cwd=None, interactive=False, mounts=None, **kwargs):
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

    def check_output(self, args, env=None, cwd=None, mounts=None, **kwargs):
        """Run a process inside a Docker container, capturing output."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            self._dockerize_args(args, mounts=mounts, env=env, cwd=cwd),
            **kwargs,
        )
