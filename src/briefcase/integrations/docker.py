from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path, PosixPath, PurePosixPath

from packaging.version import InvalidVersion, Version

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT


class XauthDatabaseCreationFailure(Exception):
    """Creating a xauth database file from the user's current X auth failed."""


class Docker(Tool):
    name = "docker"
    full_name = "Docker"

    DOCKER_VERSION_MIN = "20.10"

    WRONG_DOCKER_VERSION_ERROR = """\
Briefcase requires Docker {version_min} or higher, but you are currently running
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

      $ docker --version

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

      $ docker --version

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
            # expected output format: Docker version 25.0.2, build 29cf629\n
            docker_version = (
                tools.subprocess.check_output(
                    ["docker", "--version"],
                    env=cls.subprocess_env(),
                )
                .split("Docker version ")[1]
                .split(",")[0]
                .split("-")[0]
            )

            # Ensure Docker version is compatible
            if Version(docker_version) < Version(cls.DOCKER_VERSION_MIN):
                raise BriefcaseCommandError(
                    cls.WRONG_DOCKER_VERSION_ERROR.format(
                        version_min=cls.DOCKER_VERSION_MIN,
                        docker_version=docker_version,
                        install_url=cls.DOCKER_INSTALL_URL[tools.host_os],
                    )
                )
        except (InvalidVersion, IndexError):
            tools.logger.warning(cls.UNKNOWN_DOCKER_VERSION_WARNING)
        except subprocess.CalledProcessError:
            tools.logger.warning(cls.DOCKER_INSTALLATION_STATUS_UNKNOWN_WARNING)
        except OSError as e:
            # Docker executable doesn't exist
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
            tools.subprocess.check_output(
                ["docker", "info"],
                env=cls.subprocess_env(),
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

    @classmethod
    def _buildx_installed(cls, tools: ToolCache):
        """Verify the buildx plugin is installed."""
        try:
            tools.subprocess.check_output(
                ["docker", "buildx", "version"],
                env=cls.subprocess_env(),
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(cls.BUILDX_PLUGIN_MISSING)

    def _write_test_path(self) -> Path:
        """Host system filepath to perform write test from a container."""
        return Path.cwd() / "build/container_write_test"

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
            f"/host_write_test/{host_write_test_path.name}"
        )

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

        image_tag = "alpine" if image_tag is None else image_tag
        write_test_mounts = [
            (host_write_test_path.parent, container_write_test_path.parent)
        ]

        # Write the test file in the bind mount inside the container
        try:
            self.check_output(
                ["touch", container_write_test_path],
                image_tag=image_tag,
                mounts=write_test_mounts,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Unable to determine if Docker is mapping users"
            ) from e

        # If the file is not owned by `root`, then Docker is mapping usernames
        is_user_mapped = 0 != self.tools.os.stat(host_write_test_path).st_uid

        # Delete the file inside the container since it may be owned by root on the host
        try:
            self.check_output(
                ["rm", "-f", container_write_test_path],
                image_tag=image_tag,
                mounts=write_test_mounts,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Unable to clean up from determining if Docker is mapping users"
            ) from e

        return is_user_mapped

    @lru_cache(maxsize=None)
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
            ["docker", "images", "-q", image_tag],
            env=self.subprocess_env(),
        ).strip()

        if not image_id:
            self.tools.logger.info(
                f"Downloading Docker base image for {image_tag}...",
                prefix=self.full_name,
            )
            try:
                # disable streaming so image download progress bar is shown
                self.tools.subprocess.run(
                    ["docker", "pull", image_tag],
                    check=True,
                    stream_output=False,
                    env=self.subprocess_env(),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to obtain the Docker image for {image_tag}. "
                    "Is the image name correct?"
                ) from e

    def check_output(self, args: SubprocessArgsT, image_tag: str, **kwargs) -> str:
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
            **self.dockerize_args(args, image_tag=image_tag, **kwargs)
        )

    @classmethod
    def subprocess_env(cls, env: dict[str, str] | None = None) -> dict[str, str]:
        """Adds environment variables to the context that Docker runs in."""
        final_env = {
            # Disable the hints/recommendations that Docker prints in the console
            "DOCKER_CLI_HINTS": "false",
        }
        if env is not None:
            final_env.update(env)
        return final_env

    def dockerize_args(
        self,
        args: SubprocessArgsT,
        image_tag: str,
        interactive: bool = False,
        mounts: Iterable[tuple[str | os.PathLike, str | os.PathLike]] | None = None,
        path_map: Mapping[str | os.PathLike, str | os.PathLike] | None = None,
        env: Mapping[str, str | os.PathLike] | None = None,
        cwd: str | os.PathLike | None = None,
        add_hosts: Iterable[tuple[str, str]] | None = None,
        **subprocess_kwargs,
    ) -> dict[str, ...]:  # pragma: no-cover-if-is-windows
        """Convert arguments and environment into a Docker-compatible form.

        Converts an argument and environment specification into a form that can be used
        as arguments to invoke Docker. This involves:

         * Ensuring the run deletes the container when it exits
         * Adding volume bind mounts for specified paths
         * Injecting environment variables in to the container's session
         * Setting the current working directory for the container's session
         * Adding additional DNS entries via /etc/hosts

        :param args: The arguments for the command to be invoked
        :param image_tag: The name of the image to start the container with
        :param interactive: Start the container with stdin attached and a tty allocated
        :param mounts: Bind mounts to add to the container
        :param path_map: Mapping of files paths from the host to the container; these
            mappings are applied to all values to be dockerized
        :param env: The environment specification for the command to be executed
        :param cwd: The working directory for the command to be executed
        :param add_hosts: DNS mappings to add to the container's network
        :param subprocess_kwargs: Keyword arguments passed through in return value
        :returns: A dictionary of keyword arguments to drive subprocess calls
        """
        docker_cmdline = ["docker", "run", "--rm"]

        # Add "-it" if in interactive mode
        if interactive:
            docker_cmdline.append("-it")

        # Add volume mounts
        # The :z suffix on volume mounts allows SELinux to modify the host mount;
        # it is ignored on non-SELinux platforms
        if mounts:
            for source, target in mounts:
                docker_cmdline.extend(
                    ("--volume", f"{os.fsdecode(source)}:{os.fsdecode(target)}:z")
                )

        # Pass environment variables in as --env arguments to Docker
        if env:
            for key, value in env.items():
                docker_cmdline.extend(
                    ("--env", f"{key}={self.dockerize_path(value, path_map)}")
                )

        # Set a cwd as the working directory for the container
        if cwd:
            docker_cmdline.extend(("--workdir", self.dockerize_path(cwd, path_map)))

        # Host mappings to add to container's /etc/hosts
        if add_hosts:
            for host_name, address in add_hosts:
                docker_cmdline.extend(("--add-host", f"{host_name}:{address}"))

        # Add the image name to create the temporary container with
        docker_cmdline.append(image_tag)

        # Finally, add the command (and its arguments) to run in the container
        docker_cmdline.extend(self.dockerize_path(arg, path_map) for arg in args)

        # Augment configuration to drive the subprocess call
        subprocess_kwargs["args"] = docker_cmdline
        subprocess_kwargs["env"] = self.subprocess_env()

        return subprocess_kwargs

    def dockerize_path(
        self,
        arg: str | os.PathLike,
        path_map: Mapping[str | os.PathLike, str | os.PathLike] | None = None,
    ) -> str:  # pragma: no-cover-if-is-windows
        """Translates host file paths into the equivalent location in the docker
        filesystem as defined by a file path mapping.

        Additionally, fsdecode() is called for the input value to ensure it's something
        that can represent a path and will always be returned as a string.

        :param arg: The argument to convert to dockerized paths
        :param path_map: A mapping of host file system paths to the docker container
            file system; e.g. $HOME/.cache/briefcase -> /briefcase, such that,
            $HOME/.cache/briefcase/tools/java becomes /briefcase/tools/java
        :returns: A string where all convertible paths have been replaced
        """
        arg = os.fsdecode(arg)

        if path_map:
            for source, target in path_map.items():
                arg = arg.replace(os.fsdecode(source), os.fsdecode(target))

        return arg

    @contextlib.contextmanager
    def x11_passthrough(
        self, subprocess_kwargs: dict[str, ...]
    ) -> dict[str, ...]:  # pragma: no-cover-if-is-windows
        """Manager to expose the host's X11 server to a container.

        This allows Docker containers to use the host's X11 server with the
        authorization afforded to the current user. The user's X11 auth is copied and
        modified in a dedicated temporary xauth file. A TCP server is set up to spoof a
        new X display and proxies X commands to the current display. The XAUTHORITY
        environment variable is set to the temporary xauth file and DISPLAY is set to
        "host.docker.internal:<display number>" so that the container sends X commands
        through a Docker-provided mapping of the host's network interface to the spoofed
        display that finally proxies those commands to the actual display.

        Full docs: https://briefcase.readthedocs.io/en/latest/how-to/internal/x11passthrough.html

        :param subprocess_kwargs: Existing keywords args from the caller
        :returns: augmented keyword args for the call to subprocess
        """
        if not (DISPLAY := self.tools.os.getenv("DISPLAY")):
            raise BriefcaseCommandError(
                "The DISPLAY environment variable must be set to run an app in Docker"
            )

        # Create a TCP proxy for a spoofed X display
        proxy_popen, proxy_display_num = self._x11_tcp_proxy(DISPLAY)

        # Define the xauth database files for the spoofed display
        xauth_file_path = self._x11_proxy_display_xauth_file_path(proxy_display_num)
        docker_xauth_file_path = PurePosixPath("/tmp") / xauth_file_path.name
        try:
            # Create the xauth database file for the spoofed display
            try:
                self._x11_write_xauth_file(DISPLAY, xauth_file_path, proxy_display_num)
            except XauthDatabaseCreationFailure:
                self.tools.logger.warning(
                    """\
An X11 authentication database could not be created for the display.

Briefcase will proceed, but if access to the display is rejected, this may be why.
"""
                )
            else:
                # Add the xauth database to the container
                subprocess_kwargs.setdefault("mounts", []).append(
                    (xauth_file_path, docker_xauth_file_path)
                )
                # Tell X clients to use the xauth database to connect to the display
                subprocess_kwargs.setdefault("env", {}).update(
                    {"XAUTHORITY": docker_xauth_file_path}
                )

            # This updates the container's /etc/hosts with a mapping for
            # `host.docker.internal` to a network address for the host such that
            # network-based services on the host can be reached within the container.
            #
            # The keyword `host.docker.internal` is already always defined for
            # containers created by Docker Desktop via the DNS configured within its
            # Linux VM. However, for Docker Engine, DNS is managed by the Linux host;
            # therefore, this mapping for `host.docker.internal` must be defined each
            # time a container is started.
            #
            # The keyword `host-gateway` is interpreted and replaced with a network
            # address for the host by the Docker server when a container starts. The
            # specific network address used here will be dependent on the Docker
            # implementation, but it will likely be either the address for `docker0` or
            # and address for the host otherwise mapped through to the container.
            subprocess_kwargs.setdefault("add_hosts", []).append(
                ("host.docker.internal", "host-gateway")
            )

            # Finally, tell X clients to use the spoofed display
            subprocess_kwargs.setdefault("env", {}).update(
                {"DISPLAY": f"host.docker.internal:{proxy_display_num}"}
            )

            yield subprocess_kwargs

        finally:
            self.tools.subprocess.cleanup("X display proxy", proxy_popen)
            xauth_file_path.unlink(missing_ok=True)

    def _x11_tcp_proxy(self, DISPLAY: str) -> tuple[subprocess.Popen, int]:
        """Starts a TCP proxy as a spoofed X display.

        The TCP server's port is chosen as 6000 + the display number as defined in the
        X11 standard. In this way, when X clients attempt to make a connection for the
        chosen display number, this TCP port will be automatically evaluated by the
        client for consideration as an X display.

        The proxy is bound to 0.0.0.0 and as such will be reachable on all network
        interfaces defined for the host. Ideally, the proxy would only need to bind to
        the network bridge defined by Docker, usually `docker0`, but Docker Desktop is
        not able to use a shared network interface bridge as Docker Engine does since
        it runs containers inside a Linux VM. Instead, it attaches the host's primary
        network interface as a device on a virtual network interface bridge created by
        the VM. Because of this, the proxy must be exposed to the network at large to
        also be exposed within the container.

        :param DISPLAY: value of DISPLAY environment variable
        :returns: the Popen process for the proxy and the display number it is using
        """
        if not self.tools.shutil.which("socat"):
            raise BriefcaseCommandError(
                "Install socat to run an app for a targeted Linux distribution"
            )

        try:
            # The DISPLAY environment variable is expected to be of the form:
            #   [hostname]:[display number].[screen number]
            display_num = int(DISPLAY.split(":")[1].split(".")[0])
        except (IndexError, ValueError, AttributeError) as e:
            raise BriefcaseCommandError(
                f"Unsupported value for environment variable DISPLAY: {str(DISPLAY)!r}"
            ) from e

        proxy_display_num = self._x11_allocate_display()
        proxy_display_tcp_port = 6000 + proxy_display_num

        # If a TCP server is already running for the X display on the host, then start
        # a proxy to that TCP server for the display. While most distros do not support
        # TCP for an X display by default, X11 forwarding over SSH is facilitated by
        # opening an SSH channel on the port for the X display; so, proxying to that
        # channel allows the container to use the X display exposed by X11 forwarding.
        if self._x11_is_display_tcp(display_num):
            proxy_process = self.tools.subprocess.Popen(
                [
                    "socat",
                    f"TCP-LISTEN:{proxy_display_tcp_port},reuseaddr,fork,bind=0.0.0.0",
                    f"TCP:localhost:{6000 + display_num}",
                ]
            )

        # Otherwise, just proxy to the UNIX socket for the display
        elif self._x11_is_display_unix(display_num):
            proxy_process = self.tools.subprocess.Popen(
                [
                    "socat",
                    f"TCP-LISTEN:{proxy_display_tcp_port},reuseaddr,fork,bind=0.0.0.0",
                    f"UNIX-CONNECT:/tmp/.X11-unix/X{display_num}",
                ]
            )

        else:
            raise BriefcaseCommandError(f"Cannot find X11 display for {DISPLAY!r}")

        return proxy_process, proxy_display_num

    def _x11_proxy_display_xauth_file_path(
        self, display_num: int
    ) -> PosixPath:  # pragma: no-cover-if-is-windows
        """Path to the xauth database for the proxy display.

        The project's build directory is used to accommodate Docker Desktop. By default,
        Docker Desktop only allows bind mounts from directories/files within the user's
        home directory. So, while it may be more appropriate to use a dedicated temp
        directory, such as /tmp, this avoids having to instruct users to add that
        directory as a source of possible bind mounts.
        """
        return PosixPath.cwd() / f"build/.briefcase.docker.xauth.{display_num}"

    def _x11_allocate_display(self) -> int:
        """Finds available X display number for use; raises otherwise.

        A universal mechanism to request and reserve an X display does not exist. On
        most systems, though, there will not be many active X displays. So, this
        approach is similar to that of OpenSSH's strategy for reserving an X display
        for X11 forwarding: simply iterate over candidate display numbers using the
        first one that is not already is use.

        This check for whether a display number is already in use is limited to
        verifying a TCP server or UNIX socket does not already exist for the display.
        While other transport protocols are possible, any modern system should be using
        at least one of these transports in tandem with anything else.
        """
        # This range of candidate display numbers is arbitrary. Typically, locally
        # configured displays start at number 0 while SSH displays start at number 10.
        # So, in the common case, this is expected to return the first candidate.
        # Although, in cases where parts of this range are already allocated, the check
        # for a UNIX socket is immediate while the TCP check must actually attempt to
        # connect to the port; in practice, this should also be immediate as anything
        # listening accepts the connection or the OS rejects it since nothing is there.
        for num in range(50, 299 + 1):
            if not (self._x11_is_display_unix(num) or self._x11_is_display_tcp(num)):
                display_num = num
                break
        else:
            raise BriefcaseCommandError("Failed to allocate X11 display")

        return display_num

    def _x11_is_display_tcp(self, display_num: int) -> bool:
        """Is a TCP server running for the X display?"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            try:
                # returns 0 only if the connection is successful
                return 0 == sock.connect_ex(("localhost", 6000 + display_num))
            except OSError:
                return False

    def _x11_display_unix_socket_path(
        self, display_num: int
    ) -> PosixPath:  # pragma: no-cover-if-is-windows
        """Path to the UNIX socket for the display."""
        return PosixPath(f"/tmp/.X11-unix/X{display_num}")

    def _x11_is_display_unix(
        self, display_num: int
    ) -> bool:  # pragma: no-cover-if-is-windows
        """Is a UNIX socket running for the X display?"""
        try:
            return self._x11_display_unix_socket_path(display_num).is_socket()
        except OSError:
            return False

    def _x11_write_xauth_file(
        self,
        DISPLAY: str,
        xauth_file_path: Path,
        target_display_num: int,
    ) -> None:
        """Writes a xauth file using the current user's X authorization.

        :param DISPLAY: Value of DISPLAY environment variable
        :param xauth_file_path: File path to write xauth database for target display
        :param target_display_num: Number of targeted X display
        """
        if not self.tools.shutil.which("xauth"):
            raise BriefcaseCommandError(
                "Install xauth to run an app for a targeted Linux distribution"
            )

        # Extract the 32 byte X auth cookie for the current display
        # `xauth nlist` outputs the auth C struct defined by the libxau library
        try:
            x_display_auth_cookie = (
                self.tools.subprocess.check_output(["xauth", "-i", "nlist", DISPLAY])
                .splitlines()[0]
                .split(" ")[8]  # assumed to be a MIT-MAGIC-COOKIE-1
            )
        except (subprocess.CalledProcessError, IndexError) as e:
            raise XauthDatabaseCreationFailure("Failed to retrieve xauth cookie") from e

        # Initialize X authentication file
        xauth_file_path.parent.mkdir(parents=True, exist_ok=True)
        xauth_file_path.unlink(missing_ok=True)
        xauth_file_path.touch()

        # Create a xauth database for the target display using the current display's cookie
        try:
            self.tools.subprocess.check_output(
                [
                    "xauth",
                    "-i",
                    "-f",
                    xauth_file_path,
                    "add",
                    f":{target_display_num}",
                    "MIT-MAGIC-COOKIE-1",
                    x_display_auth_cookie,
                ]
            )
        except subprocess.CalledProcessError as e:
            raise XauthDatabaseCreationFailure(
                "Failed to add a xauth entry for existing cookie"
            ) from e

        # Retrieve xauth list that was just written for the target display
        try:
            xauth_list = self.tools.subprocess.check_output(
                ["xauth", "-i", "-f", xauth_file_path, "nlist"]
            )
        except subprocess.CalledProcessError as e:
            raise XauthDatabaseCreationFailure("Failed to retrieve xauth list") from e

        # When an X auth entry is added to a xauth database, the auth is tied to a
        # hostname and a display number. Since this X auth will be used to connect to
        # the host machine's X server via a proxy exposed within the container, those
        # connections will be using a different hostname for the display. Therefore,
        # this replaces the hostname in the auth entry with the "FamilyWild" tag which
        # allows using the auth for the display regardless of the targeted hostname.
        xauth_list = "\n".join("ffff" + line[4:] for line in xauth_list.splitlines())

        # Re-write xauth for target display to support any target hostname
        try:
            self.tools.subprocess.check_output(
                ["xauth", "-i", "-f", xauth_file_path, "nmerge", "-"],
                input=xauth_list,
            )
        except subprocess.CalledProcessError as e:
            raise XauthDatabaseCreationFailure(
                "Failed to merge xauth updates for FamilyWild hostname"
            ) from e


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
        extra_build_args: list[str] | None = None,
        **kwargs,
    ) -> DockerAppContext:  # pragma: no-cover-if-is-windows
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
            extra_build_args=extra_build_args,
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
        extra_build_args: list[str] | None = None,
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
            # Install requirements for both building *and* running the app
            # (ensure a copy of system_requires is used to avoid modification)
            system_requires = getattr(self.app, "system_requires", []).copy()
            system_requires.extend(getattr(self.app, "system_runtime_requires", []))

            with self.tools.logger.context("Docker"):
                try:
                    self.tools.subprocess.run(
                        [
                            "docker",
                            "buildx",
                            "build",
                            "--load",
                            "--progress",
                            "plain",
                            "--tag",
                            self.image_tag,
                            "--file",
                            dockerfile_path,
                            "--build-arg",
                            f"SYSTEM_REQUIRES={' '.join(system_requires)}",
                            "--build-arg",
                            f"HOST_UID={self.tools.os.getuid()}",
                            "--build-arg",
                            f"HOST_GID={self.tools.os.getgid()}",
                            Path(
                                self.app_base_path,
                                *self.app.sources[0].split("/")[:-1],
                            ),
                        ]
                        + (extra_build_args if extra_build_args is not None else []),
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    raise BriefcaseCommandError(
                        f"Error building Docker container image for {self.app.app_name}."
                    ) from e

    @contextlib.contextmanager
    def run_app_context(self, subprocess_kwargs: dict[str, ...]) -> dict[str, ...]:
        """Manager to run a Briefcase project app in a container.

        :returns: context manager to wrap the call to Popen/run/check_output()
        """
        with self.tools.docker.x11_passthrough(subprocess_kwargs) as subprocess_kwargs:
            yield subprocess_kwargs

    def run(self, args: SubprocessArgsT, **kwargs) -> None:
        """Run a process inside a Docker container."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.run()" behaves as closely to
        # "subprocess.run()" as possible.
        if kwargs.get("interactive"):
            kwargs["stream_output"] = False

        with self.tools.logger.context("Docker"):
            self.tools.subprocess.run(**self._dockerize_args(args, **kwargs))

    def check_output(self, args: SubprocessArgsT, **kwargs) -> str:
        """Capture and return output from a process inside a Docker container."""
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.check_output()" behaves as closely to
        # "subprocess.check_output()" as possible.
        return self.tools.subprocess.check_output(
            **self._dockerize_args(args, **kwargs)
        )

    def Popen(self, args: SubprocessArgsT, **kwargs) -> subprocess.Popen:
        """Open and return a process running inside a Docker container."""
        return self.tools.subprocess.Popen(**self._dockerize_args(args, **kwargs))

    def _dockerize_args(
        self, args: SubprocessArgsT, **kwargs
    ) -> dict[str, ...]:  # pragma: no-cover-if-is-windows
        """App-specific wrapper for Docker.dockerize_args().

        Uses the app's dedicated Docker image to run the container.

        Adds app's bundle directory and the Briefcase data directory as bind mounts.

        All bind mount definitions also serve as path mappings from the host in to the
        container file system; these mappings are applied to the command arguments,
        environment variable values, and the working directory.
        """
        kwargs["image_tag"] = self.image_tag

        kwargs.setdefault("mounts", []).extend(
            [
                (self.host_bundle_path, "/app"),
                (self.host_data_path, self.docker_briefcase_path),
            ]
        )

        kwargs.setdefault("path_map", {}).update(dict(kwargs["mounts"]))

        # Convert fully-qualified paths for the host's Python to the unqualified Python
        # binary available inside the container
        kwargs["path_map"][sys.executable] = f"python{self.python_version}"

        return self.tools.docker.dockerize_args(args, **kwargs)
