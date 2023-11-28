import subprocess

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError

from ...utils import create_file, file_content


@pytest.mark.parametrize("verbose", [True, False])
def test_thin_binary(dummy_command, verbose, tmp_path, capsys):
    """A thin binary is left as-is."""
    if verbose:
        dummy_command.logger.verbosity = LogLevel.VERBOSE

    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-original")

    # Mock the result of the "lipo info" call.
    dummy_command.tools.subprocess.check_output.return_value = (
        "Non-fat file: path/to/file.dylib is architecture: gothic\n"
    )

    # Thin the binary; this is effectively a no-op
    dummy_command.ensure_thin_binary(
        tmp_path / "path/to/file.dylib",
        arch="gothic",
    )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was *not* invoked
    dummy_command.tools.subprocess.run.assert_not_called()

    # The original file is unmodified.
    assert file_content(tmp_path / "path/to/file.dylib") == "dylib-original"

    # Output only happens if in debug mode
    output = capsys.readouterr().out.split("\n")
    assert len(output) == (2 if verbose else 1)


@pytest.mark.parametrize("verbose", [True, False])
def test_fat_dylib(dummy_command, verbose, tmp_path, capsys):
    """A fat binary library can be thinned."""
    if verbose:
        dummy_command.logger.verbosity = LogLevel.VERBOSE

    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-fat")

    # Mock the result of the "lipo info" call.
    dummy_command.tools.subprocess.check_output.return_value = (
        "Architectures in the fat file: path/to/file.dylib are: modern gothic\n"
    )

    # Mock the result of successfully thinning a library
    def thin_dylib(*args, **kwargs):
        create_file(args[0][args[0].index("-output") + 1], "dylib-thin")

    dummy_command.tools.subprocess.run.side_effect = thin_dylib

    # Thin the binary to the "gothic" architecture
    dummy_command.ensure_thin_binary(
        tmp_path / "path/to/file.dylib",
        arch="gothic",
    )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was invoked
    dummy_command.tools.subprocess.run.assert_called_once_with(
        [
            "lipo",
            "-thin",
            "gothic",
            "-output",
            tmp_path / "path/to/file.dylib.gothic",
            tmp_path / "path/to/file.dylib",
        ],
        check=True,
    )

    # The original file now has the thinned content.
    assert file_content(tmp_path / "path/to/file.dylib") == "dylib-thin"

    # Output only happens if in debug mode
    output = capsys.readouterr().out.split("\n")
    assert len(output) == (2 if verbose else 1)


@pytest.mark.parametrize("verbose", [True, False])
def test_fat_dylib_arch_mismatch(dummy_command, verbose, tmp_path, capsys):
    """If a fat binary doesn't contain the target architecture, an error is raised."""
    if verbose:
        dummy_command.logger.verbosity = LogLevel.VERBOSE

    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-fat")

    # Mock the result of the "lipo info" call.
    dummy_command.tools.subprocess.check_output.return_value = (
        "Architectures in the fat file: path/to/file.dylib are: modern artdeco\n"
    )

    # Thin the binary to the "gothic" architecture. This will raise an exception
    with pytest.raises(
        BriefcaseCommandError,
        match=r"file\.dylib does not contain a gothic slice",
    ):
        dummy_command.ensure_thin_binary(
            tmp_path / "path/to/file.dylib",
            arch="gothic",
        )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was *not* invoked
    dummy_command.tools.subprocess.run.assert_not_called()


@pytest.mark.parametrize("verbose", [True, False])
def test_fat_dylib_unknown_info(dummy_command, verbose, tmp_path, capsys):
    """If the lipo info call succeeds, but generates unknown output, an error is
    raised."""
    if verbose:
        dummy_command.logger.verbosity = LogLevel.VERBOSE

    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-fat")

    # Mock the result of the "lipo info" call.
    dummy_command.tools.subprocess.check_output.return_value = (
        "This is unexpected output...\n"
    )

    # Thin the binary to the "gothic" architecture. This will raise an exception
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to determine architectures in .*file\.dylib",
    ):
        dummy_command.ensure_thin_binary(
            tmp_path / "path/to/file.dylib",
            arch="gothic",
        )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was *not* invoked
    dummy_command.tools.subprocess.run.assert_not_called()


def test_lipo_info_fail(dummy_command, tmp_path):
    """If lipo can't inspect a binary, an error is raised."""
    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-fat")

    # Mock the result of the "lipo info" call.
    dummy_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(cmd="lipo -info", returncode=-1)
    )

    # Thin the binary to the "gothic" architecture. This will raise an exception
    with pytest.raises(
        BriefcaseCommandError, match=r"Unable to inspect architectures in .*file\.dylib"
    ):
        dummy_command.ensure_thin_binary(
            tmp_path / "path/to/file.dylib",
            arch="gothic",
        )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was not invoked
    dummy_command.tools.subprocess.run.assert_not_called()


@pytest.mark.parametrize("verbose", [True, False])
def test_lipo_thin_fail(dummy_command, verbose, tmp_path, capsys):
    """If lipo fails thinning the binary, an error is raised."""
    if verbose:
        dummy_command.logger.verbosity = LogLevel.VERBOSE

    # Create a source binary.
    create_file(tmp_path / "path/to/file.dylib", "dylib-fat")

    # Mock the result of the "lipo -info" call.
    dummy_command.tools.subprocess.check_output.return_value = (
        "Architectures in the fat file: path/to/file.dylib are: modern gothic\n"
    )

    # Mock the result of the failed "lipo -thin" call.
    dummy_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="lipo -thin", returncode=-1
    )

    # Thin the binary to the "gothic" architecture. This will raise an exception
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to create thin binary from .*file.dylib",
    ):
        dummy_command.ensure_thin_binary(
            tmp_path / "path/to/file.dylib",
            arch="gothic",
        )

    # Lipo -info was invoked
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "lipo",
            "-info",
            tmp_path / "path/to/file.dylib",
        ],
    )

    # Lipo -thin was invoked
    dummy_command.tools.subprocess.run.assert_called_once_with(
        [
            "lipo",
            "-thin",
            "gothic",
            "-output",
            tmp_path / "path/to/file.dylib.gothic",
            tmp_path / "path/to/file.dylib",
        ],
        check=True,
    )

    # The original file is unmodified.
    assert file_content(tmp_path / "path/to/file.dylib") == "dylib-fat"

    # Output only happens if in debug mode
    output = capsys.readouterr().out.split("\n")
    assert len(output) == (2 if verbose else 1)
