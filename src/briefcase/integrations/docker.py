import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


def verify_docker(command):
    """
    Verify that docker is available.
    """
    try:
        # If no JRE/JDK is installed, /usr/libexec/java_home
        # raises an error.
        output = command.subprocess.check_output(
            ['docker', '--version'],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        ).strip('\n')

        # Do a simple check that the docker that was invoked
        # actually looks like the real deal. If it is,
        #
        if not output.startswith('Docker version '):
            raise BriefcaseCommandError("""
""")

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Couldn't invoke docker.
        if command.host_os == 'Windows':
            install_url = "https://docs.docker.com/docker-for-windows/install/"
            extra_content = ""
        elif command.host_os == 'Darwin':
            install_url = "https://docs.docker.com/docker-for-mac/install/"
            extra_content = ""
        else:
            install_url = "https://docs.docker.com/engine/install/#server"
            extra_content = """
Alternatively, to run briefcase natively (i.e. without Docker), use the
`--no-docker` command-line argument.
"""
        raise BriefcaseCommandError("""
Briefcase requires Docker, but it is not installed (or is not on your PATH).
Visit:

    {install_url}

to download and install git manually.
{extra_content}
If you have installed docker recently and are still getting this error, you may
need to restart your terminal session.
""".format(
            install_url=install_url,
            extra_content=extra_content,
        ))

    # Return the docker wrapper
    return Docker


class Docker:
    def __init__(self, command, app):
        self.command = command
        self._subprocess = command.subprocess
        self.app = app

    def build_image(self):
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
                    "-t", self.command.docker_image_tag(self.app),
                    "-f", self.command.bundle_path(self.app) / 'Dockerfile',
                    "--build-arg", "PY_VERSION={command.python_version_tag}".format(
                        command=self.command
                    ),
                    "--build-arg", "SYSTEM_REQUIRES={system_requires}".format(
                        system_requires=system_requires
                    ),
                    str(Path.cwd() / "src")
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
            "--volume", "{self.command.dot_briefcase_path}:/root/.briefcase".format(
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
                        str(self.command.dot_briefcase_path), '/root/.briefcase'
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
