# install_requirement.py - Install a requirement from a PEP 517 project
#
# Usage
# -----
# $ python install_requirement.py [-h] [--extra EXTRA] [--project-root PROJECT_ROOT] [requirements ...]
#
# Install one or more PEP 517 project defined requirements
#
# positional arguments:
#   requirements          List of project requirements to install. Any project
#                         requirements that start with any of these values will
#                         be installed. For instance, including 'pytest' in this
#                         list would install both pytest and pytest-xdist.
#
# options:
#   -h, --help            show this help message and exit
#   --extra EXTRA         Name of the extra where the requirements are defined
#   --project-root PROJECT_ROOT
#                         File path to the root of the project. The current
#                         directory is used by default.
#
# Purpose
# -------
# Installs one or more requested requirements as defined for the project.
#
# In certain workflows, such as automated coverage reporting, the coverage
# dependencies must be installed first. Since a project's requirements are often
# pinned to specific versions to ensure consistency for the project regardless of the
# environment, the coverage dependencies that are installed should match those pinned
# for the project.
#
# A simple method to accomplish this is ``pip install .[dev]`` in which ``pip`` will
# build the source and install the project with all its defined requirements. However,
# this is very inefficient when only one or a few specific requirements are needed.
#
# Therefore, this script will evaluate the requirements defined in the project's
# metadata and install the ones matching those being requested to be installed.
#
# Dependencies
# ------------
# The ``build``, ``setuptools``, and ``wheel`` packages must be installed to run.

from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from shutil import get_terminal_size

from build.util import project_wheel_metadata
from packaging.requirements import Requirement


class RequirementsInstallerError(Exception):
    def __init__(self, msg: str, error_no: int):
        self.msg = msg
        self.error_no = error_no


class HelpText(RequirementsInstallerError):
    """Shows script's help text."""


class NoRequirementsFound(RequirementsInstallerError):
    """No project requirements were found to install."""


def parse_args():
    width = max(min(get_terminal_size().columns, 80) - 2, 20)
    parser = ArgumentParser(
        description="Installs one or more PEP 517 project defined requirements",
        formatter_class=lambda prog: RawDescriptionHelpFormatter(prog, width=width),
    )
    parser.add_argument(
        "requirements",
        type=str,
        nargs="*",
        help=(
            "List of project requirements to install. If the project defines extras for "
            "a requirement, do not include them in this list; they will be included "
            "automatically when the requirement is installed. For instance, if "
            "coverage[toml] is a project requirement, just include coverage in this list."
        ),
    )
    parser.add_argument(
        "--extra",
        type=str,
        default="",
        help="Name of the extra where the requirements are defined",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=".",
        help=(
            "File path to the root of the project. The current directory is used by "
            "default."
        ),
    )

    args = parser.parse_args()

    if not args.requirements:
        raise HelpText(parser.format_help(), error_no=-1)

    return args


def gather_requirements(
    project_root: str | Path,
    requested_requirements: list[str],
    extra_name: str = "",
) -> list[Requirement]:
    """Identifies one or more matching requirements from a project."""
    project_root = Path(project_root).resolve()
    project_metadata = project_wheel_metadata(project_root, isolated=False)
    project_requirements = [
        requirement
        for requirement in map(Requirement, project_metadata.get_all("Requires-Dist"))
        if not requirement.marker or requirement.marker.evaluate({"extra": extra_name})
    ]

    matching_requirements = [
        requirement
        for requirement in project_requirements
        if requirement.name in requested_requirements
    ]

    if not matching_requirements:
        raise NoRequirementsFound(
            f"No requirements matched requested requirements: "
            f"{', '.join(requested_requirements)}\n\n"
            f"The requirements below were evaluated for matching:\n "
            f"{f'{chr(10)} '.join(req.name for req in project_requirements)}",
            error_no=1,
        )

    return matching_requirements


def install_requirements(requirements: list[Requirement]):
    """Install requirements from PyPI."""
    for requirement in requirements:
        extras = f"[{','.join(requirement.extras)}]" if requirement.extras else ""
        requirement_str = f"{requirement.name}{extras}{requirement.specifier}"
        print(f"Installing {requirement_str}...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                requirement_str,
            ],
            check=True,
        )


def main():
    ret_code = 0
    try:
        args = parse_args()
        requirements_to_install = gather_requirements(
            project_root=args.project_root,
            requested_requirements=args.requirements,
            extra_name=args.extra,
        )
        install_requirements(requirements=requirements_to_install)
    except RequirementsInstallerError as e:
        print(e.msg)
        ret_code = e.error_no

    return ret_code


if __name__ == "__main__":
    sys.exit(main())
