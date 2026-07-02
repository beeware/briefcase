import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("args", "expected_suffix"),
    [
        ([sys.executable], []),
        (
            [sys.executable, "-m", "pip", "install", "package"],
            ["-m", "pip", "install", "package"],
        ),
        (
            [Path(sys.executable), "-c", "print('hello')"],
            ["-c", "print('hello')"],
        ),
    ],
)
def test_rewrite_args_replaces_system_python(venv, args, expected_suffix):
    """The head argument is replaced when it equals sys.executable."""
    result = venv.rewrite_args(args)
    assert result == [
        "conda",
        "run",
        "--prefix",
        venv.venv_path,
        Path(sys.executable).name,
        *expected_suffix,
    ]


def test_rewrite_args_non_python(venv):
    """Non-python commands are executed in the conda environment."""
    result = venv.rewrite_args(["pip", "install", "-U", "things"])
    assert result == [
        "conda",
        "run",
        "--prefix",
        venv.venv_path,
        "pip",
        "install",
        "-U",
        "things",
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_rewrite_args_case_insensitive(venv):
    """On Windows, `rewrite_args` is case-insensitive."""
    result = venv.rewrite_args([sys.executable.lower(), "-V"])
    assert result == [
        "conda",
        "run",
        "--prefix",
        venv.venv_path,
        Path(sys.executable).name,
        "-V",
    ]
