from __future__ import annotations

import argparse
import io

import pytest

from briefcase.commands.config import ConfigCommand


class DummyConsole:
    def __init__(self):
        self.buf = io.StringIO()

    def print(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def info(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")


def make_parser():
    """Build a parser with ConfigCommand.add_options() applied."""
    cmd = ConfigCommand(console=DummyConsole())
    parser = argparse.ArgumentParser(prog="briefcase config", add_help=False)
    cmd.add_options(parser)
    return parser


def test_default_values_when_no_args():
    parser = make_parser()
    ns = parser.parse_args([])
    # --global absent -> False
    assert getattr(ns, "global_scope", False) is False
    # Mode flags default to None/False
    assert getattr(ns, "get", None) is None
    assert getattr(ns, "unset", None) is None
    assert getattr(ns, "list", False) is False
    # Positionals default to None
    assert getattr(ns, "key", None) is None
    assert getattr(ns, "value", None) is None


def test_global_scope_flag_sets_dest():
    parser = make_parser()
    ns = parser.parse_args(["--global"])
    assert ns.global_scope is True


def test_get_mode_parses_value():
    parser = make_parser()
    ns = parser.parse_args(["--get", "author.email"])
    assert ns.get == "author.email"
    assert ns.unset is None
    assert ns.list is False


def test_unset_mode_parses_value():
    parser = make_parser()
    ns = parser.parse_args(["--unset", "android.device"])
    assert ns.unset == "android.device"
    assert ns.get is None
    assert ns.list is False


def test_list_mode_parses_flag_only():
    parser = make_parser()
    ns = parser.parse_args(["--list"])
    assert ns.list is True
    assert ns.get is None
    assert ns.unset is None


def test_set_mode_parses_positionals():
    parser = make_parser()
    ns = parser.parse_args(["author.name", "Jane Developer"])
    assert ns.key == "author.name"
    assert ns.value == "Jane Developer"
    # No mutually exclusive mode set
    assert ns.get is None and ns.unset is None and ns.list is False


@pytest.mark.parametrize(
    "args",
    [
        ["--get", "author.email", "--unset", "author.email"],  # get + unset
        ["--get", "author.email", "--list"],  # get + list
        ["--unset", "author.email", "--list"],  # unset + list
    ],
)
def test_modes_are_mutually_exclusive(args):
    parser = make_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(args)
