import os
import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


class Docker:
    WRONG_DOCKER_VERSION_ERROR = """\
Briefcase requires Docker 19 or higher, but you are currently running
version {docker_version}. Visit:

    {install_url}

to download and install an updated version of Docker.
{extra_content}
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
{extra_content}
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

    # Platform-specific template context dictionary for Docker installation details
    DOCKER_INSTALL_DETAILS = {
        "Windows": {
            "install_url": "https://docs.docker.com/docker-for-windows/install/",
            "extra_content": "",
        },
        "Darwin": {
            "install_url": "https://docs.docker.com/docker-for-mac/install/",
            "extra_content": "",
        },
        "Linux": {
            "install_url": "https://docs.docker.com/engine/install/#server",
            "extra_content": "Alternatively, to run briefcase natively (i.e. without Docker), use the\n"
            "`--no-docker` command-line argument.",
        },
    }

    def __init__(self, tools):
        self.tools = tools

    @classmethod
    def verify(cls, tools):
        """Verify Docker is installed and operational."""
        # short circuit since already verified and available
        if hasattr(tools, "docker"):
            return tools.docker

        # Verify Docker version is compatible.
        try:
            # Try to get the version of docker that is installed.
            output = tools.subprocess.check_output(
                ["docker", "--version"],
                stderr=subprocess.STDOUT,
            ).strip("\n")

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
                            **cls.DOCKER_INSTALL_DETAILS[tools.host_os],
                        )
                    )

            else:
                tools.logger.warning(cls.UNKNOWN_DOCKER_VERSION_WARNING)
        except subprocess.CalledProcessError:
            tools.logger.warning(cls.DOCKER_INSTALLATION_STATUS_UNKNOWN_WARNING)
        except FileNotFoundError as e:
            # Docker executable doesn't exist.
            raise BriefcaseCommandError(
                cls.DOCKER_NOT_INSTALLED_ERROR.format(
                    **cls.DOCKER_INSTALL_DETAILS[tools.host_os]
                )
            ) from e

        # Verify Docker is operational for user.
        try:
            # Invoke a docker command to check if the daemon is running,
            # and the user has sufficient permissions.
            # We don't care about the output, just that it succeeds.
            tools.subprocess.check_output(
                ["docker", "info"],
                stderr=subprocess.STDOUT,
            )
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

        tools.docker = Docker(tools=tools)
        return tools.docker


class DockerAppContext:
    def __init__(self, tools, app):
        self.tools = tools
        self.app = app

        self.app_base_path = None
        self.host_platform_path = None
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
        tools,
        app,
        image_tag: str,
        dockerfile_path: Path,
        app_base_path: Path,
        host_platform_path: Path,
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
        :param host_platform_path: Base directory for where App is built
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
            host_platform_path=host_platform_path,
            host_data_path=host_data_path,
            python_version=python_version,
        )
        return tools[app].app_context

    def prepare(
        self,
        image_tag: str,
        dockerfile_path: Path,
        app_base_path: Path,
        host_platform_path: Path,
        host_data_path: Path,
        python_version: str,
    ):
        """Create/update the Docker image from the app's Dockerfile."""
        self.app_base_path = app_base_path
        self.host_platform_path = host_platform_path
        self.host_data_path = host_data_path
        self.image_tag = image_tag
        self.python_version = python_version

        self.tools.logger.info(
            "Building Docker container image...",
            prefix=self.app.app_name,
        )
        with self.tools.input.wait_bar("Building Docker image..."):
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
                        f"PY_VERSION={self.python_version}",
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
        * any path in <platform path> into the equivalent stemming from /app
        * any path in <data path> into the equivalent in ~/.cache/briefcase

        :param arg: The string argument to convert to dockerized paths
        :returns: A string where all convertible paths have been replaced.
        """
        if arg == sys.executable:
            return f"python{self.python_version}"
        arg = arg.replace(os.fsdecode(self.host_platform_path), "/app")
        arg = arg.replace(os.fsdecode(self.host_data_path), self.docker_data_path)

        return arg

    def _dockerize_args(self, args, env=None):
        """Convert arguments and environment into a Docker-compatible form.
        Convert an argument and environment specification into a form that can
        be used as arguments to invoke Docker. This involves:

         * Configuring the Docker invocation to reference the
           appropriate container image, and clean up afterwards
         * Setting volume mounts for the container instance
         * Transforming any references to local paths into Docker path references.

        :param args: The arguments for the command to be invoked
        :param env: The environment specification for the command to be executed
        :returns: A list of arguments that can be used to invoke the command
            inside a docker container.
        """
        # The :z suffix on volume mounts allows SELinux to modify the host
        # mount; it is ignored on non-SELinux platforms.
        docker_args = [
            "docker",
            "run",
            "--volume",
            f"{self.host_platform_path}:/app:z",
            "--volume",
            f"{self.host_data_path}:{self.docker_data_path}:z",
            "--rm",
        ]

        # If any environment variables have been defined, pass them in
        # as --env arguments to Docker.
        if env:
            for key, value in env.items():
                docker_args.extend(["--env", f"{key}={self._dockerize_path(value)}"])

        # ... then the image name to create the temporary container with
        docker_args.append(self.image_tag)

        # ... then add the command (and its arguments) to run in the container
        docker_args.extend([self._dockerize_path(str(arg)) for arg in args])

        return docker_args

    def run(self, args, env=None, **kwargs):
        """Run a process inside a Docker container."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.run()" behaves as closely to
        # "subprocess.run()" as possible.
        self.tools.logger.info("Entering Docker context...", prefix=self.app.app_name)
        self.tools.subprocess.run(
            self._dockerize_args(args, env=env),
            **kwargs,
        )
        self.tools.logger.info("Leaving Docker context", prefix=self.app.app_name)

    def check_output(self, args, env=None, **kwargs):
        """Run a process inside a Docker container, capturing output."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            self._dockerize_args(args, env=env),
            **kwargs,
        )
