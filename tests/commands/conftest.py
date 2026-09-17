from unittest.mock import MagicMock

import git as git_
import pytest

# A sample git hash; prefix with `sha1:` to use in calls
TEMPLATE_COMMIT_HEXSHA = "e8082ea4d3310d7605e12f4ab1fa7ff7b637b974"


@pytest.fixture
def mock_git():
    git = MagicMock(spec_set=git_)
    git.exc = git_.exc
    # Give the git repo a known hash value
    clone_head = git.Repo.clone_from.return_value.remote.return_value.refs
    clone_head.__getitem__.return_value.commit.hexsha = TEMPLATE_COMMIT_HEXSHA
    return git
