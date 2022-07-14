from unittest.mock import MagicMock

from briefcase.integrations.visualstudio import VisualStudio


def test_managed_install(tmp_path):
    """All Visual Studio installs are unmanaged."""
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    visualstudio = VisualStudio(MagicMock(), msbuild_path=msbuild_path)

    assert not visualstudio.managed_install


def test_msbuild_path(tmp_path):
    """The MSBUild path is the one used for construction."""
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    visualstudio = VisualStudio(MagicMock(), msbuild_path=msbuild_path)

    assert visualstudio.msbuild_path == msbuild_path


def test_install_metadata(tmp_path):
    """Install metadata can be provided and retrieved."""
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    install_metadata = {
        "instanceId": "deadbeef",
        "installDate": "2022-07-14T10:42:37Z",
    }
    visualstudio = VisualStudio(
        MagicMock(),
        msbuild_path=msbuild_path,
        install_metadata=install_metadata,
    )

    assert visualstudio.install_metadata["instanceId"] == "deadbeef"
    assert visualstudio.install_metadata["installDate"] == "2022-07-14T10:42:37Z"


def test_no_install_metadata(tmp_path):
    """Install metadata is optional."""
    msbuild_path = tmp_path / "Visual Studio" / "MSBuild.exe"
    visualstudio = VisualStudio(MagicMock, msbuild_path=msbuild_path)

    assert visualstudio.install_metadata is None
