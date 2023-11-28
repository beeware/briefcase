import os
import sys
from unittest.mock import MagicMock, PropertyMock

import pytest
import requests

from briefcase.console import Console, Log
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import GradlePackageCommand

from ....utils import create_file


@pytest.fixture
def package_command(tmp_path, first_app_config, monkeypatch):
    command = GradlePackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.android_sdk = MagicMock(spec_set=AndroidSDK)
    command.tools.os = MagicMock(spec_set=os)
    command.tools.os.environ = {}
    command.tools.sys = MagicMock(spec_set=sys)
    command.tools.requests = MagicMock(spec_set=requests)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    monkeypatch.setattr(
        type(command.tools), "system_encoding", PropertyMock(return_value="ISO-42")
    )

    # Make sure the dist folder exists
    (tmp_path / "base_path/dist").mkdir(parents=True)
    return command


@pytest.fixture
def first_app_generated(first_app_config, tmp_path):
    # Create the briefcase.toml file
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "briefcase.toml",
        """
[paths]
app_packages_path="app_packages"
support_path="support"
metadata_resource_path="res/briefcase.xml"
""",
    )

    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "res"
        / "briefcase.xml",
        """<resources></resources>""",
    )
    return first_app_config
