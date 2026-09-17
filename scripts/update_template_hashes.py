#!/usr/bin/env python3
"""Pin the current commit hash for each of Briefcase's official templates.

Run this as part of cutting a release, after confirming every template has a
branch for the new version. It resolves the `sha1:<hexsha>` value for each
template's release branch and writes it directly into the corresponding
`app_template_hash`/`template_hash` class attribute, flagging any repository
that doesn't have a branch for the requested version yet.

Usage:
    python scripts/update_template_hashes.py [version] [--dry-run]

If `version` isn't provided, the version of the currently-installed Briefcase
package is used (with any dev/pre-release suffix stripped). If `--dry-run` is
given, the hashes that would be written are printed, but no files are modified.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from packaging.version import Version

import briefcase

#: Every template repository Briefcase clones by default, and the file/class/
#: attribute that pins its expected hash. This list must be kept in sync with
#: the checklist in docs/en/how-to/internal/release.md step 4.
TEMPLATES = [
    (
        "https://github.com/beeware/briefcase-template",
        "src/briefcase/commands/new.py",
        "NewCommand.template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-macOS-app-template.git",
        "src/briefcase/platforms/macOS/app.py",
        "macOSAppCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-macOS-Xcode-template.git",
        "src/briefcase/platforms/macOS/xcode.py",
        "macOSXcodeCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-windows-app-template.git",
        "src/briefcase/platforms/windows/app.py",
        "WindowsAppCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-windows-VisualStudio-template.git",
        "src/briefcase/platforms/windows/visualstudio.py",
        "WindowsVisualStudioCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-linux-appimage-template.git",
        "src/briefcase/platforms/linux/appimage.py",
        "LinuxAppImageCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-linux-flatpak-template.git",
        "src/briefcase/platforms/linux/flatpak.py",
        "LinuxFlatpakCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-linux-system-template.git",
        "src/briefcase/platforms/linux/system.py",
        "LinuxSystemCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-android-gradle-template.git",
        "src/briefcase/platforms/android/gradle.py",
        "GradleCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-iOS-Xcode-template.git",
        "src/briefcase/platforms/iOS/xcode.py",
        "iOSXcodeCreateCommand.app_template_hash",
    ),
    (
        "https://github.com/beeware/briefcase-web-static-template.git",
        "src/briefcase/platforms/web/static.py",
        "StaticWebCreateCommand.app_template_hash",
    ),
]


def resolve_branch_hexsha(repo_url: str, branch: str) -> str | None:
    """Look up the commit hash of a branch on a remote repository.

    :param repo_url: The URL of the git repository.
    :param branch: The name of the branch to resolve.
    :returns: The 40-character commit hash, or `None` if the branch doesn't
        exist on the remote.
    """
    result = subprocess.run(
        ["git", "ls-remote", "--heads", repo_url, branch],
        capture_output=True,
        text=True,
        check=True,
    )
    line = result.stdout.strip()
    if not line:
        return None
    return line.split()[0]


def compute_update(
    source_file: Path,
    attribute: str,
    new_hexsha: str,
) -> tuple[str, str]:
    """Locate the pinned-hash line for `attribute` in `source_file`, and compute its
    replacement text.

    `source_file` isn't modified by this function; the caller decides when
    (or whether) to write `new_text` back to disk.

    :param source_file: Path to the Python source file containing the
        attribute assignment.
    :param attribute: The bare attribute name (e.g. `template_hash`) to
        search for. Any `ClassName.` prefix must already be stripped by the
        caller.
    :param new_hexsha: The new 40-character commit hash to pin.
    :returns: A 2-tuple of `(old_hexsha, new_text)`, where `old_hexsha` is
        the 40-character hash that was previously pinned, and `new_text` is
        the full contents of `source_file` with that line updated.
    :raises RuntimeError: If a line matching
        `{attribute} = "sha1:<40 hex chars>"` isn't found exactly once in
        `source_file`.
    """
    text = source_file.read_text()
    pattern = re.compile(
        r"^(?P<prefix>[ \t]*"
        + re.escape(attribute)
        + r'[ \t]*=[ \t]*)"sha1:(?P<hexsha>[0-9a-f]{40})"[ \t]*$',
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one line matching "
            f'`{attribute} = "sha1:<hexsha>"` in {source_file}, found '
            f"{len(matches)}."
        )
    old_hexsha = matches[0].group("hexsha")
    new_text = pattern.sub(
        rf'\g<prefix>"sha1:{new_hexsha}"',
        text,
        count=1,
    )
    return old_hexsha, new_text


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments for this script.

    :param argv: The argument list to parse (excluding the program name).
    :returns: The parsed arguments, with `.version` (`str | None`) and
        `.dry_run` (`bool`) attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Resolve and pin the commit hash for each of Briefcase's "
            "official templates."
        ),
    )
    parser.add_argument(
        "version",
        nargs="?",
        default=None,
        help=(
            "The Briefcase version being released (e.g. 1.2.3). Defaults "
            "to the version of the currently-installed Briefcase package."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=("Print the hashes that would be pinned, without modifying any files."),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    branch = args.version
    if branch is None:
        branch = f"v{Version(briefcase.__version__).base_version}"

    print(f"Resolving template hashes for branch {branch!r}...\n")

    missing = []
    resolved = []
    for repo_url, source_file, attribute in TEMPLATES:
        print(f"Checking {repo_url}...")
        hexsha = resolve_branch_hexsha(repo_url, branch)
        if hexsha is None:
            missing.append(repo_url)
            print(f"  - no branch {branch!r} found")
        else:
            resolved.append((repo_url, source_file, attribute, hexsha))

    if missing:
        print(
            f"\n{len(missing)} repositories are missing branch {branch!r}. "
            "Push the branch before re-running this script."
        )
        return 1

    updates = []
    for _repo_url, source_file, attribute, new_hexsha in resolved:
        bare_attribute = attribute.rsplit(".", 1)[-1]
        old_hexsha, new_text = compute_update(
            Path(source_file),
            bare_attribute,
            new_hexsha,
        )
        updates.append((source_file, attribute, old_hexsha, new_hexsha, new_text))

    if args.dry_run:
        print("\nDry run - no files were modified. Would update:")
        for source_file, attribute, old_hexsha, new_hexsha, _new_text in updates:
            print(
                f"  {source_file}: {attribute} = "
                f'"sha1:{old_hexsha}" -> "sha1:{new_hexsha}"'
            )
        return 0

    print()
    for source_file, attribute, _old_hexsha, new_hexsha, new_text in updates:
        Path(source_file).write_text(new_text)
        print(f'Updated {source_file}: {attribute} = "sha1:{new_hexsha}"')

    print(
        "\nReview the changes above with `git diff`, then commit them "
        "before tagging the release."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
