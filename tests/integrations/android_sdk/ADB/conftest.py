import pytest

from briefcase.integrations.base import ToolCache


@pytest.fixture
def mock_tools(mock_tools, android_sdk, tmp_path) -> ToolCache:
    # add Android SDK to mock tools
    mock_tools.android_sdk = android_sdk
    return mock_tools
