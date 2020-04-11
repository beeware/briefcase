import pytest


def test_sdk_url(mock_sdk):
    "Validate that the SDK URL is computed using `host_os`."
    # We set `host_os` to a sentinel value in order to validate that
    # `build_command.sdk_url` uses `host_os`.
    mock_sdk.command.host_os = "sAMple"

    assert mock_sdk.sdk_url == (
        "https://dl.google.com/android/repository/sdk-tools-sample-4333796.zip"
    )


@pytest.mark.parametrize(
    "host_os, sdkmanager_name",
    [
        ("Windows", "sdkmanager.bat"),
        ("NonWindows", "sdkmanager")
    ],
)
def test_sdkmanager_path(mock_sdk, host_os, sdkmanager_name):
    """Validate that if the user is on Windows, we run `sdkmanager.bat`,
    otherwise, `sdkmanager`."""
    # Mock out `host_os` so we can test Windows when not on Windows.
    mock_sdk.command.host_os = host_os

    assert mock_sdk.sdkmanager_path == (
        mock_sdk.root_path / "tools" / "bin" / sdkmanager_name
    )


def test_simple_env(mock_sdk, tmp_path):
    "The SDK Environment can be constructed"
    assert mock_sdk.env == {
        'JAVA_HOME': '/path/to/jdk',
        'ANDROID_SDK_ROOT': str(tmp_path / 'sdk')
    }


def test_override_env(mock_sdk, tmp_path):
    "The existing environment is preserved, but overwritten by SDK variables"
    mock_sdk.command.os.environ = {
        'other': 'stuff',
        'JAVA_HOME': '/other/jdk',
        'ANDROID_SDK_ROOT': '/other/android_sdk',
    }

    assert mock_sdk.env == {
        'other': 'stuff',
        'JAVA_HOME': '/path/to/jdk',
        'ANDROID_SDK_ROOT': str(tmp_path / 'sdk')
    }
