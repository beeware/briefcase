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
                raise BriefcaseCommandError("""
Briefcase requires Docker 19 or higher, but you are currently running
version {docker_version}. Visit:

    {install_url}

to download and install an updated version of Docker.
{extra_content}""".format(
                    docker_version=docker_version,
                    **docker_install_details(command.host_os)
                ))

        else:
            print("""
*************************************************************************
** WARNING: Unable to determine the version of Docker                  **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     docker --version

   from the command prompt.

*************************************************************************
""")
    except subprocess.CalledProcessError:
        print("""
*************************************************************************
** WARNING: Unable to determine if Docker is installed                 **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     docker --version

   from the command prompt.

*************************************************************************
""")
    except FileNotFoundError:
        # Docker executable doesn't exist.
        raise BriefcaseCommandError("""
Briefcase requires Docker, but it is not installed (or is not on your PATH).
Visit:

    {install_url}

to download and install git manually.
{extra_content}
If you have installed Docker recently and are still getting this error, you may
need to restart your terminal session.
""".format(**docker_install_details(command.host_os)))

    # Return the Docker wrapper
    return Docker


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
                    Path(str(self.command.base_path), *self.app.sources[0].split('/')[:-1])
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
        docker_args = [
            "docker", "run",
            "--interactive",
            "--tty",
            "--volume", "{self.command.platform_path}:/app".format(
                self=self
            ),
            "--volume", "{self.command.dot_briefcase_path}:/home/brutus/.briefcase".format(
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
            elif str(self.command.platform_path) in arg:
                docker_args.append(
                    arg.replace(str(self.command.platform_path), '/app')
                )
            elif str(self.command.dot_briefcase_path) in arg:
                docker_args.append(
                    arg.replace(
                        str(self.command.dot_briefcase_path), '/home/brutus/.briefcase'
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
