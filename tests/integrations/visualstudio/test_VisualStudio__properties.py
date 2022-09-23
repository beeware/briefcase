from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.visualstudio import VisualStudio


@pytest.fixture
def visualstudio(mock_tools, tmp_path) -> VisualStudio:
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    return VisualStudio(mock_tools, msbuild_path=msbuild_path)


def test_managed_install(visualstudio, tmp_path):
    """All Visual Studio installs are unmanaged."""
    assert not visualstudio.managed_install


def test_msbuild_path(visualstudio, tmp_path):
    """The MSBuild path is the one used for construction."""
    assert visualstudio.msbuild_path == tmp_path / "Visual Studio" / "MSBuild.exe"


def test_install_metadata(tmp_path):
    """Install metadata can be provided and retrieved."""
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    install_metadata = {
        "instanceId": "deadbeef",
        "installDate": "2022-07-14T10:42:37Z",
    }
    visualstudio = VisualStudio(
        MagicMock(spec_set=ToolCache),
        msbuild_path=msbuild_path,
        install_metadata=install_metadata,
    )

    assert visualstudio.install_metadata["instanceId"] == "deadbeef"
    assert visualstudio.install_metadata["installDate"] == "2022-07-14T10:42:37Z"


def test_no_install_metadata(visualstudio, tmp_path):
    """Install metadata is optional."""
    assert visualstudio.install_metadata is None
