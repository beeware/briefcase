import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.system import LinuxSystemBuildCommand


@pytest.fixture
def build_command(dummy_console, tmp_path, first_app):
    command = LinuxSystemBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"first": first_app},
    )
    command.tools.host_os = "Linux"
    command.tools.host_arch = "wonky"

    # Mock subprocess
    command.tools.subprocess = MagicMock()

    return command


@pytest.mark.parametrize(
    ("cache_output", "original", "expected"),
    [
        # (Truncated) output of gcc, a regular package.
        (
            "Package: gcc\nVersions: \n4:13.2.0-7ubuntu1 (/var/lib/apt/lists/ports.ubuntu...\n Description Language: \n                 File: /var/lib/apt/lists/ports.ubuntu...\n                  MD5: c7efd71c7c651a9ac8b2adf36b137790\n\n\nReverse Depends: \n  nodeenv,gcc 4:4.9.1\n  rustc-1.85,gcc\n  cmake,gcc\n  cargo,gcc\nDependencies: \n4:13.2.0-7ubuntu1 - cpp (5 4:13.2.0-7ubuntu1) ... \nProvides: \n4:13.2.0-7ubuntu1 - gcc:arm64 (= 4:13.2.0-7ubuntu1) \nReverse Provides: \n",
            "gcc",
            None,
        ),
        # Make reverse-provides make-guile, but also provides make
        (
            "Package: make\nVersions: \n4.3-4.1build2 (/var/lib/apt/lists/ports.ubuntu...\n Description Language: \n                 File: /var/lib/apt/lists/ports.ubuntu...\n                  MD5: 3ef13fe0be8e85cb535b13ff062ae8eb\n\n\nReverse Depends: \n  make-doc,make 3.80+3.81.rc2-1\n  dh-make,make\n  cmake,make\nDependencies: \n4.3-4.1build2 - libc6 (2 2.38) make-guile ...\nProvides: \n4.3-4.1build2 - make:any (= 4.3-4.1build2) \nReverse Provides: \nmake-guile 4.3-4.1build2 (= 4.3-4.1build2)\n",
            "make",
            None,
        ),
        # libqt6gui6 is provided by a virtual package, with a single reverse-provides
        (
            "Package: libqt6gui6\nVersions: \n\nReverse Depends: \n  libqt6gui6t64,libqt6gui6 6.4.2+dfsg-21.1build5\n  libqt6gui6t64,libqt6gui6\nDependencies: \nProvides: \nReverse Provides: \nlibqt6gui6t64 6.4.2+dfsg-21.1build5 (= 6.4.2+dfsg-21.1build5)\n",
            "libqt6gui6",
            "libqt6gui6t64",
        ),
        # libglib2.0 is a virtual package with multiple reverse-provides
        (
            "Package: libglib2.0-0\nVersions: \n\nReverse Depends: \n  libglib2.0-0t64,libglib2.0-0 2.80.0-6ubuntu3~]\n  libglib2.0-0t64,libglib2.0-0 2.80.0-6ubuntu3~\n  ffmpegthumbnailer,libglib2.0-0\n  libglib2.0-0t64,libglib2.0-0 2.79.4\nDependencies: \nProvides: \nReverse Provides: \nlibglib2.0-0t64 2.80.0-6ubuntu3.4 (= 2.80.0-6ubuntu3.4)\nlibglib2.0-0t64 2.80.0-6ubuntu3.5 (= 2.80.0-6ubuntu3.5)\nlibglib2.0-0t64 2.80.0-6ubuntu1 (= 2.80.0-6ubuntu1)\n",
            "libglib2.0-0",
            "libglib2.0-0t64",
        ),
        # mail-transport-agent is a virtual package, but one that provides multiple
        # inconsistent reverse-provides
        (
            "Package: mail-transport-agent\nVersions: \n\nReverse Depends: \n  anacron,mail-transport-agent\n  anope,mail-transport-agent\nDependencies: \nProvides: \nReverse Provides: \nexim4-daemon-light 4.97-4ubuntu4.3 (= )\nexim4-daemon-heavy 4.97-4ubuntu4.3 (= )\nssmtp 2.64-11build2 (= )\n",
            "mail-transport-agent",
            None,
        ),
    ],
)
def test_deb_devirtualize(build_command, cache_output, original, expected):
    """Debian requirements can be verified."""

    # Mock the effect of checking requirements that are all present
    build_command.tools.subprocess.check_output.return_value = cache_output

    # Devirtualize the package
    assert build_command._deb_devirtualize(original) == expected

    # The packages were verified
    build_command.tools.subprocess.check_output.assert_called_once_with(
        ["apt-cache", "showpkg", original], quiet=1
    )


def test_deb_devirtualize_fail(build_command):
    """If Debian devirtualiztaio fails, an error is raised."""

    # Mock the effect of apt-cache failing
    build_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(cmd="apt-cache", returncode=1)
    )

    # Devirtualize the package
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to check apt-cache package record for 'missing'",
    ):
        build_command._deb_devirtualize("missing")

    # An attempt was made to check the cache
    build_command.tools.subprocess.check_output.assert_called_once_with(
        ["apt-cache", "showpkg", "missing"], quiet=1
    )
