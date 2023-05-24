from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

from build.util import project_wheel_metadata
from packaging.requirements import Requirement


def parse_args():
    parser = ArgumentParser(
        prog="Dependency Installer",
        description="Install one or more project dependencies",
    )
    parser.add_argument(
        "dependencies",
        type=str,
        nargs="*",
        help="One or more dependencies to install",
    )
    parser.add_argument(
        "--extra",
        type=str,
        default="",
        help="Name of the extra where the dependencies are defined",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=".",
        help="File path to the root of the project",
    )
    return parser.parse_args()


def gather_requirements(
    project_root: str | Path,
    requested_deps: list[str],
    extra_name: str = "",
) -> list[Requirement]:
    """Identifies one or more matching requirements from a project."""
    project_root = Path(project_root).resolve()
    project_metadata = project_wheel_metadata(project_root, isolated=False)
    project_reqs = [
        req
        for req in map(Requirement, project_metadata.get_all("Requires-Dist"))
        if not req.marker or req.marker.evaluate(environment={"extra": extra_name})
    ]

    found_requirements = [
        requirement
        for requirement in project_reqs
        if any(requirement.name.startswith(dep) for dep in requested_deps)
    ]

    if not found_requirements:
        deps_str = "\n ".join(d.name for d in project_reqs)
        print(f"One or more dependencies not found; considered:\n {deps_str}")

    return found_requirements


def install_requirements(requirements: list[Requirement]):
    """Install requirements from PyPI."""
    for requirement in requirements:
        requirement_str = f"{requirement.name}{requirement.specifier}"
        print(f"Installing {requirement_str}...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                # "-q",
                "install",
                "--upgrade",
                requirement_str,
            ],
            check=True,
        )

    return 0


def main():
    args = parse_args()
    install_requirements(
        requirements=gather_requirements(
            project_root=args.project_root,
            requested_deps=args.dependencies,
            extra_name=args.extra,
        )
    )


if __name__ == "__main__":
    main()
