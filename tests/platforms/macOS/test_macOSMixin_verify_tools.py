import platform
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_verify_macos_cpu_arch(dummy_command):
    """Running through Rosetta on macOS will raise an error."""
    # Create a Mock object for the platform module
    dummy_command.tools.platform = MagicMock(spec_set=platform)

    # Simulate that Mock platform is running on Apple Silicon with an x86_64 Python interpreter
    dummy_command.tools.platform.machine = MagicMock(return_value="x86_64")
    dummy_command.tools.platform.version = MagicMock(return_value="ARM64")

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"The Python interpreter that is being used to run Briefcase has been "
            r"compiled for x86_64, and is running in emulation mode on Apple "
            r"Silicon hardware. You must use a Python interpreter that has been "
            r"compiled for Apple Silicon, or is a Universal binary."
        ),
    ):
        dummy_command.verify_tools()
