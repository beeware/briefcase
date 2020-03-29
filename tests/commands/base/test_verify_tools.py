from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(base_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    integrations = mock.MagicMock()
    integrations.git.verify_git_is_installed.side_effect = BriefcaseCommandError(
        "Briefcase requires git, but it is not installed"
    )
    base_command.integrations = integrations

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        base_command.verify_tools()


def test_base_tools_exist(base_command):
    "If all the required base tools exist, verification passes"

    # This assumes git is actually in the test environment. If it isn't,
    # this test will fail.
    base_command.verify_tools()
