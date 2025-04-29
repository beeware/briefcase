from unittest import mock


def test_all_config_files_are_used(base_command, mock_git):
    """Read the system, global, user, and repo config files."""
    base_command.tools.git = mock_git
    mock_git.config.get_config_path.side_effect = ["file1", "file2", "file3"]

    base_command.get_git_config_value("test-section", "test-option")

    assert mock_git.config.get_config_path.call_args_list == [
        mock.call("system"),
        mock.call("global"),
        mock.call("user"),
    ]
    expected_config_files = ["file1", "file2", "file3", ".git/config"]
    mock_git.config.GitConfigParser.assert_called_once_with(expected_config_files)
