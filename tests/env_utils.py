import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from textwrap import dedent


def helptext(script_name: str):
    """Print help text for the environment utilities."""
    print(
        dedent(
            f"""\
            usage: {script_name} <env-util-name> [arg1 arg2 ...]"

            Utilities

            install-req > installs a dev requirement from setup.cfg, e.g.:
                {script_name} install-req tox
            """
        )
    )


def install_requirement(requirement_name: str) -> int:
    """Installs a dev requirement from setup.cfg."""
    config = ConfigParser()
    config.read(Path(__file__).parent.parent / "setup.cfg")

    found = False
    for requirement in config.get("options.extras_require", "dev").split("\n"):
        if requirement.startswith(requirement_name):
            requirement = requirement.replace(" ", "")
            print(f"Installing {requirement}...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "-q",
                    "install",
                    "--upgrade",
                    requirement,
                ]
            )
            found = True
    if found:
        return 0
    else:
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        helptext(sys.argv[0])
        sys.exit(-1)

    util_name = sys.argv[1]
    util_args = sys.argv[2:]

    if util_name == "install-req":
        sys.exit(install_requirement(*util_args))

    print(f"No environment utility found for {util_name!r}")
    sys.exit(-2)
