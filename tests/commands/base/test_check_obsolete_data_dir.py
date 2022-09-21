import os
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import InfoHelpText

from .conftest import DummyCommand


def test_skip_if_dot_briefcase_nonexistent(capsys, tmp_path):
    """Obsolete data dir check does not run if .briefcase dir does not
    exist."""

    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.input.boolean_input = MagicMock()

    cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_not_called()
    assert not dot_briefcase_dir.exists()
    assert capsys.readouterr().out == ""


def test_skip_if_data_dir_from_environment(monkeypatch, capsys, tmp_path):
    """If the data directory came from the user environment, don't run the
    check, even if .briefcase exists."""
    monkeypatch.setenv("BRIEFCASE_HOME", os.fsdecode(tmp_path / "custom"))

    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    dot_briefcase_dir.mkdir(parents=True)

    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.input.boolean_input = MagicMock()

    cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_not_called()
    assert dot_briefcase_dir.exists()
    assert capsys.readouterr().out == ""


def test_first_notice_if_dot_briefcase_exists(capsys, tmp_path):
    """Obsolete data dir check shows full notice of transition if .briefcase
    directory exists but new data directory does not exist."""
    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    dot_briefcase_dir.mkdir(parents=True)

    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.input.boolean_input = MagicMock()
    cmd.input.boolean_input.return_value = True

    cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_called_once()
    assert dot_briefcase_dir.exists()
    assert cmd.data_path.exists()
    assert "Briefcase is changing its data directory" in capsys.readouterr().out


def test_subsequent_notice_if_dot_briefcase_exists(capsys, tmp_path):
    """Obsolete data dir check shows notice of transition if .briefcase
    directory exists and new data directory exists."""
    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    dot_briefcase_dir.mkdir(parents=True)

    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.data_path.mkdir(parents=True)
    cmd.input.boolean_input = MagicMock()

    cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_not_called()
    assert dot_briefcase_dir.exists()
    assert cmd.data_path.exists()
    assert "Briefcase is no longer using the data directory" in capsys.readouterr().out


def test_exception_if_user_does_not_continue(capsys, tmp_path):
    """Exception is raised if user does not want to continue after transition
    notice."""
    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    dot_briefcase_dir.mkdir(parents=True)

    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.input.boolean_input = MagicMock()
    cmd.input.boolean_input.return_value = False

    with pytest.raises(InfoHelpText, match="Move the Briefcase data directory from:"):
        cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_called_once()
    assert dot_briefcase_dir.exists()
    assert not cmd.data_path.exists()
    assert "Briefcase is changing its data directory" in capsys.readouterr().out


def test_automatic_continue_if_input_not_enabled(capsys, tmp_path):
    """Execution continues after initial notice if --no-input is specified."""
    home_path = tmp_path / "home"
    dot_briefcase_dir = home_path / ".briefcase"
    dot_briefcase_dir.mkdir(parents=True)

    cmd = DummyCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data_dir",
    )
    cmd.tools.home_path = home_path
    cmd.input.enabled = False
    cmd.input.boolean_input = MagicMock()

    cmd.check_obsolete_data_dir()

    cmd.input.boolean_input.assert_called_once()
    assert dot_briefcase_dir.exists()
    assert cmd.data_path.exists()
    assert "Briefcase is changing its data directory" in capsys.readouterr().out
