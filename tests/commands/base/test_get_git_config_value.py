import itertools
from unittest import mock
from unittest.mock import MagicMock


def test_all_config_files_are_read(base_command, mock_git):
    """All git config files are read (system, global, user, repo)."""
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


def test_config_values_are_parsed(base_command, tmp_path, monkeypatch):
    """If the requested value exists in one of the config files, it shall be returned."""
    import git

    # use 'real' gitpython library (no mock)
    base_command.tools.git = git

    # mock `git.config.get_config_path` to always provide the same three local files
    mock_config_paths = ["missing-file-1", "config-1", "missing-file-2"]
    git.config.get_config_path = MagicMock()
    git.config.get_config_path.side_effect = itertools.cycle(mock_config_paths)

    # create local two config files
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config-1").write_text("[user]\n\tname = Some User\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text(
        "[user]\n\temail = my@email.com\n", encoding="utf-8"
    )

    # expect values are parsed from all existing config files
    assert base_command.get_git_config_value("user", "name") == "Some User"
    assert base_command.get_git_config_value("user", "email") == "my@email.com"

    # expect that missing sections and options are handled
    assert base_command.get_git_config_value("user", "something") is None
    assert base_command.get_git_config_value("something", "something") is None
