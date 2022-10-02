from collections import namedtuple

import pytest

from briefcase.console import Log
from briefcase.integrations.subprocess import get_process_id_by_command

Process = namedtuple("Process", "info")
process_list_one_proc = [
    Process(
        info=dict(cmdline=["/bin/cmd.sh", "--input", "data"], create_time=20, pid=100)
    )
]

process_list_two_procs_diff_cmd = [
    Process(
        info=dict(
            cmdline=["/bin/first_cmd.sh", "--input", "data"], create_time=20, pid=100
        )
    ),
    Process(
        info=dict(
            cmdline=["/bin/second_cmd.sh", "--input", "data"], create_time=10, pid=200
        )
    ),
]

process_list_two_procs_same_cmd = [
    Process(
        info=dict(cmdline=["/bin/cmd.sh", "--input", "data"], create_time=20, pid=100)
    ),
    Process(
        info=dict(cmdline=["/bin/cmd.sh", "--input", "data"], create_time=10, pid=200)
    ),
]


@pytest.mark.parametrize(
    ("process_list", "command_list", "expected_pid", "expected_stdout"),
    [
        ([], ["/bin/cmd.sh", "--input", "data"], None, ""),
        (process_list_one_proc, ["/bin/cmd.sh", "--input", "data"], 100, ""),
        (process_list_one_proc, ["/bin/random_cmd.sh", "--input", "data"], None, ""),
        (
            process_list_two_procs_diff_cmd,
            ["/bin/first_cmd.sh", "--input", "data"],
            100,
            "",
        ),
        (
            process_list_two_procs_diff_cmd,
            ["/bin/random_cmd.sh", "--input", "data"],
            None,
            "",
        ),
        (
            process_list_two_procs_same_cmd,
            ["/bin/cmd.sh", "--input", "data"],
            100,
            "Multiple running instances of app found. "
            "Using most recently created app process 100.\n",
        ),
        (
            process_list_two_procs_same_cmd,
            ["/bin/random_cmd.sh", "--input", "data"],
            None,
            "",
        ),
    ],
)
def test_get_process_id_by_command_w_command_line(
    process_list,
    command_list,
    expected_pid,
    expected_stdout,
    monkeypatch,
    capsys,
):
    """Finds correct process for command line or returns None."""
    monkeypatch.setattr("psutil.process_iter", lambda attrs: process_list)
    found_pid = get_process_id_by_command(command_list=command_list, logger=Log())
    assert found_pid == expected_pid
    assert capsys.readouterr().out == expected_stdout


@pytest.mark.parametrize(
    ("process_list", "command", "expected_pid", "expected_stdout"),
    [
        ([], "/bin/cmd.sh", None, ""),
        (process_list_one_proc, "/bin/cmd", 100, ""),
        (process_list_one_proc, "/bin/cmd.sh --input data", None, ""),
        (process_list_one_proc, "/bin/cmd.sh", 100, ""),
        (process_list_one_proc, "/bin/random_cmd.sh", None, ""),
        (process_list_two_procs_diff_cmd, "/bin/first_cmd.sh", 100, ""),
        (process_list_two_procs_diff_cmd, "/bin/random_cmd.sh", None, ""),
        (
            process_list_two_procs_same_cmd,
            "/bin/cmd.sh",
            100,
            "Multiple running instances of app found. "
            "Using most recently created app process 100.\n",
        ),
        (process_list_two_procs_same_cmd, "/bin/random_cmd.sh", None, ""),
    ],
)
def test_get_process_id_by_command_w_command(
    process_list,
    command,
    expected_pid,
    expected_stdout,
    monkeypatch,
    capsys,
):
    """Finds correct process for command or returns None."""
    monkeypatch.setattr("psutil.process_iter", lambda attrs: process_list)
    found_pid = get_process_id_by_command(command=command, logger=Log())
    assert found_pid == expected_pid
    assert capsys.readouterr().out == expected_stdout


def test_get_process_id_no_logging(monkeypatch, capsys):
    """If no logger is provided, warnings about ambiguous matches aren't
    printed."""
    monkeypatch.setattr(
        "psutil.process_iter",
        lambda attrs: process_list_two_procs_same_cmd,
    )
    found_pid = get_process_id_by_command(
        command_list=["/bin/cmd.sh", "--input", "data"]
    )
    assert found_pid == 100
    assert capsys.readouterr().out == ""
