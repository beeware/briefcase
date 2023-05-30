from unittest.mock import MagicMock

import git as git_
import pytest


@pytest.fixture
def mock_git():
    git = MagicMock(spec_set=git_)
    git.exc = git_.exc
    return git
