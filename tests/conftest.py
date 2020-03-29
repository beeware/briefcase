from unittest import mock

import pytest
from git import exc as git_exceptions


@pytest.fixture
def mock_git():
    git = mock.MagicMock()
    git.exc = git_exceptions

    return git
