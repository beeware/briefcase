import sys

import pytest


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "original, dockerized",
    [
        # Simple values are unmodified
        ("value", "value"),
        # sys.executable is replaced with the
        (
            "/path/to/python",
            "python3.X",
        ),
        # bundle path is replaced with /app
        (
            "{tmp_path}/platform/path/to/file",
            "/app/path/to/file",
        ),
        # data path is replaced with ~brutus/.cache/briefcase
        (
            "{tmp_path}/briefcase/path/to/file",
            "/home/brutus/.cache/briefcase/path/to/file",
        ),
        # Multiple references in a single path are converted
        (
            "/unmodified/path:{tmp_path}/platform/path/to/file:{tmp_path}/briefcase/path/to/other/file",
            "/unmodified/path:/app/path/to/file:/home/brutus/.cache/briefcase/path/to/other/file",
        ),
    ],
)
def test_dockerize_path(
    mock_docker_app_context,
    tmp_path,
    monkeypatch,
    original,
    dockerized,
):
    monkeypatch.setattr("sys.executable", "/path/to/python")

    assert (
        mock_docker_app_context._dockerize_path(original.format(tmp_path=tmp_path))
        == dockerized
    )
