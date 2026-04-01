from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


# test the verify_tools method of the macOSMixin class,
# to ensure that it raises the expected error when running on Apple Silicon
# with an x86_64 Python interpreter
def test_verify_tools_on_macos(dummy_command):
    """If you're on macOS, you can verify tools."""
    # Simulate running on Apple Silicon with an x86_64 Python interpreter
    dummy_command.tools.platform.machine = MagicMock(return_value="x86_64")
    dummy_command.tools.platform.version = MagicMock(return_value="ARM64")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"The Python interpreter that is being used to run Briefcase has been compiled for x86_64, and is running in emulation mode on Apple Silicon hardware. You must use a Python interpreter that has been compiled for Apple Silicon, or is a Universal binary.",
    ):
        dummy_command.verify_tools()
