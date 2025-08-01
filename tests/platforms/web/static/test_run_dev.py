import re

import pytest

from briefcase.console import Console
from briefcase.exceptions import UnsupportedCommandError
from briefcase.platforms.web.static import StaticWebDevCommand


@pytest.fixture
def dev_command(tmp_path):
    return StaticWebDevCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_run_dev_app_unsupported(dev_command, first_app_built):
    with pytest.raises(
        UnsupportedCommandError,
        match=re.escape(
            "The dev command for the web static format has not been implemented (yet!)."
        ),
    ):
        dev_command.run_dev_app(first_app_built, env={})
