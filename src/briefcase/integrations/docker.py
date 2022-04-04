import os
import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


def docker_install_details(host_os):
    """
    Obtain a platform-specific template context dictionary for Docker
    installation details.

    :param host_os: The host OS for which installation details are required.
    :returns: a context dictionary containing Docker installation details.
    """
    if host_os == 'Windows':
        install_url = "https://docs.docker.com/docker-for-windows/install/"
        extra_content = ""
    elif host_os == 'Darwin':
        install_url = "https://docs.docker.com/docker-for-mac/install/"
        extra_content = ""
    else:
        install_url = "https://docs.docker.com/engine/install/#server"
        extra_content = """Alternatively, to run briefcase natively (i.e. without Docker), use the
`--no-docker` command-line argument.
"""
    return {
        'install_url': install_url,
        'extra_content': extra_content,
    }


def verify_docker(command):
    """
    Verify that docker is available.

    :param command: The command that needs to perform the verification check.
    """

    WRONG_DOCKER_VERSION_ERROR = """
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
    DOCKER_NOT_INSTALLED_ERROR = """
Briefcase requires Docker, but it is not installed (or is not on your PATH).
Visit:

    {install_url}

to download and install git manually.
{extra_content}
If you have installed Docker recently and are still getting this error, you may
need to restart your terminal session.
"""
    try:
        # Try to get the version of docker that is installed.
        output = command.subprocess.check_output(
            ['docker', '--version'],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        ).strip('\n')

        # Do a simple check that the docker that was invoked
        # actually looks like the real deal, and is a version that
        # meets our requirements.
        if output.startswith('Docker version '):
            docker_version = output[15:]
            version = docker_version.split('.')
            if int(version[0]) < 19:
                # Docker version isn't compatible.
                raise BriefcaseCommandError(
                    WRONG_DOCKER_VERSION_ERROR.format(
                        docker_version=docker_version,
                        **docker_install_details(command.host_os),
                    )
                )

        else:
            print(UNKNOWN_DOCKER_VERSION_WARNING)
    except subprocess.CalledProcessError:
        print(DOCKER_INSTALLATION_STATUS_UNKNOWN_WARNING)
    except FileNotFoundError:
        # Docker executable doesn't exist.
        raise BriefcaseCommandError(
            DOCKER_NOT_INSTALLED_ERROR.format(
                **docker_install_details(command.host_os)
            )
        )

    # Check that docker commands can actually run.
    _verify_docker_can_run(command)

    # Return the Docker wrapper
    return Docker


def _verify_docker_can_run(command):
    """
    Verify that the user has sufficient permissions, and that the Docker
    daemon is running.

    This is done by attempting to run a low-impact command (docker info)
    that requires both permissions and a working daemon.

    :param command: The command that needs to perform the verification check.
    """

    LACKS_PERMISSION_ERROR = """
Docker has been installed, but Briefcase is unable to invoke
Docker commands. It is possible that your user does not have
permissions to invoke Docker.

See https://docs.docker.com/engine/install/linux-postinstall/
for details on configuring access to your Docker installation.
"""

    DAEMON_NOT_RUNNING_ERROR = """
Briefcase is unable to use Docker commands. It appears the Docker
daemon is not running.

See https://docs.docker.com/config/daemon/ for details on how to
configure your Docker daemon.
"""

    GENERIC_DOCKER_ERROR = """
Briefcase was unable to use Docker commands. Check your Docker
installation, and try again.
"""

    try:
        # Invoke a docker command to check if the daemon is running,
        # and the user has sufficient permissions.
        # We don't care about the output, just that it succeeds.
        command.subprocess.check_output(
            ['docker', 'info'],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        ).strip('\n')
    except subprocess.CalledProcessError as e:
        failure_output = e.output
        if 'permission denied while trying to connect' in failure_output:
            raise BriefcaseCommandError(LACKS_PERMISSION_ERROR)
        elif (
            # error message on Ubuntu
            'Is the docker daemon running?' in failure_output
            # error message on macOS
            or 'connect: connection refused' in failure_output
        ):
            raise BriefcaseCommandError(DAEMON_NOT_RUNNING_ERROR)
        else:
            raise BriefcaseCommandError(GENERIC_DOCKER_ERROR)


class Docker:
    def __init__(self, command, app):
        self.command = command
        self._subprocess = command.subprocess
        self.app = app

    def prepare(self):
        try:
            print()
            print("[{app.app_name}] Building Docker container image...".format(app=self.app))
            print()
            try:
                system_requires = ' '.join(self.app.system_requires)
            except AttributeError:
                system_requires = ''

            self._subprocess.run(
                [
                    "docker", "build",
                    "--tag", self.command.docker_image_tag(self.app),
                    "--file", self.command.bundle_path(self.app) / 'Dockerfile',
                    "--build-arg", "PY_VERSION={command.python_version_tag}".format(
                        command=self.command
                    ),
                    "--build-arg", "SYSTEM_REQUIRES={system_requires}".format(
                        system_requires=system_requires
                    ),
                    "--build-arg", "HOST_UID={uid}".format(uid=self.command.os.getuid()),
                    "--build-arg", "HOST_GID={gid}".format(gid=self.command.os.getgid()),
                    Path(self.command.base_path, *self.app.sources[0].split('/')[:-1])
                ],
                check=True,
            )

        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Error building Docker container for {app.app_name}.".format(app=self.app)
            )

    def run(self, args, env=None, **kwargs):
        "Run a process inside the Docker container"
        # Set up the `docker run` invocation in interactive mode,
        # with volume mounts for the platform and .briefcase directories.
        # The :z suffix allows SELinux to modify the host mount; it is ignored
        # on non-SELinux platforms.
        docker_args = [
            "docker", "run",
            "--tty",
            "--volume", "{self.command.platform_path}:/app:z".format(
                self=self
            ),
            "--volume", "{self.command.dot_briefcase_path}:/home/brutus/.briefcase:z".format(
                self=self
            ),
        ]

        # If any environment variables have been defined, pass them in
        # as --env arguments to Docker.
        if env:
            for key, value in env.items():
                docker_args.extend([
                    '--env', "{key}={value}".format(key=key, value=value)
                ])

        # ... then the image name.
        docker_args.append(self.command.docker_image_tag(self.app))

        # ... then add all the arguments
        for arg in args:
            arg = str(arg)
            if arg == sys.executable:
                docker_args.append(
                    'python{command.python_version_tag}'.format(
                        command=self.command
                    )
                )
            elif os.fsdecode(self.command.platform_path) in arg:
                docker_args.append(
                    arg.replace(os.fsdecode(self.command.platform_path), '/app')
                )
            elif os.fsdecode(self.command.dot_briefcase_path) in arg:
                docker_args.append(
                    arg.replace(
                        os.fsdecode(self.command.dot_briefcase_path), '/home/brutus/.briefcase'
                    )
                )
            else:
                docker_args.append(arg)

        # Invoke the process.
        # Any exceptions from running the process are *not* caught.
        # This ensures that "docker.run()" behaves as closely to
        # "subprocess.run()" as possible.
        self._subprocess.run(
            docker_args,
            **kwargs,
        )
