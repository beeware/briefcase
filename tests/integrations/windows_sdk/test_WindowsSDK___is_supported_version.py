import pytest

from briefcase.integrations.windows_sdk import WindowsSDK


@pytest.mark.parametrize(
    "sdk_version, supported",
    [
        ("42.42.1000", True),
        ("42.42.1000.0", True),
        ("42.42.1001.001", True),
        ("42.42.1001.0.dev", True),
        ("42.42.1001.asdf", True),
        ("42.42.123456789", True),
        ("42.42.123456789.10", True),
        ("42.42.950", False),
        ("42.42.950.50", False),
        ("42.42.NaN.50", False),
        ("42", False),
        ("42.42", False),
        ("41.41.1000", False),
        (42.42, False),
        (42, False),
    ],
)
def test_winsdk_version_validation(
    mock_tools,
    sdk_version,
    supported,
    tmp_path,
    monkeypatch,
):
    """Evaluation of the proposed SDK version is correct."""
    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "42.42")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 1000)

    windows_sdk = WindowsSDK(
        tools=mock_tools,
        root_path=tmp_path / "win_sdk",
        version=sdk_version,
        arch="x64",
    )

    # Verify the version
    assert WindowsSDK._is_supported_version(windows_sdk) is supported
