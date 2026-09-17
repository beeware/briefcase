import pytest

from ...utils import create_file


@pytest.mark.parametrize(
    "args",
    [
        # Empty list of args
        [],
        # Non-file references
        ["--foo", "bar"],
        ["--foo", ".file"],
        # Non-existent relative references
        ["--foo", "./does-not-exist"],
        ["--foo", "../does-not-exist"],
        ["--foo", "./somewhere/does-not-exist"],
        ["--foo", "../somewhere/does-not-exist"],
    ],
)
def test_no_op(mock_tools, args, tmp_path):
    """File paths that aren't existent relative references are unchanged."""
    assert mock_tools.file.resolve_relative_args(args, tmp_path / "deep/other") == args


@pytest.mark.parametrize(
    "args",
    [
        ["--foo", "bar"],
        ["--foo", ".file"],
    ],
)
def test_no_op_existing(mock_tools, args, tmp_path):
    """Non-file references that do match filenames aren't transformed."""
    create_file((tmp_path / "tools" / args[1]).resolve(), "content")

    assert mock_tools.file.resolve_relative_args(args, tmp_path / "deep/other") == args


@pytest.mark.parametrize(
    "args",
    [
        # Existent relative references
        ["--foo", "./does-not-exist"],
        ["--foo", "../does-not-exist"],
        ["--foo", "./somewhere/does-not-exist"],
        ["--foo", "../somewhere/does-not-exist"],
    ],
)
def test_transformed(mock_tools, args, tmp_path):
    """File paths that are existent relative references are transformed."""
    create_file((tmp_path / "deep/other" / args[1]).resolve(), "content")

    assert mock_tools.file.resolve_relative_args(args, tmp_path / "deep/other") == [
        args[0],
        (tmp_path / "deep/other" / args[1]).resolve(),
    ]
