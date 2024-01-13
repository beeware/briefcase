import sys
from pathlib import Path, PurePosixPath

import pytest


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "original, path_map, dockerized",
    [
        # Simple values are unmodified
        ("value", None, "value"),
        # sys.executable is replaced with the specified version
        (
            "/path/to/python",
            {"/path/to/python": "python3.X", "/base/briefcase": "/briefcase"},
            "python3.X",
        ),
        # bundle path is replaced with /app
        (
            "/base/bundle/path/to/file",
            {"/base/bundle": "/app", "/base/briefcase": "/briefcase"},
            "/app/path/to/file",
        ),
        # data path is replaced with /briefcase
        (
            "/base/briefcase/path/to/file",
            {"/base/bundle": "/app", "/base/briefcase": "/briefcase"},
            "/briefcase/path/to/file",
        ),
        # Path inputs are converted
        (
            PurePosixPath("/base/briefcase/path/to/file"),
            {"/base/bundle": "/app", "/base/briefcase": "/briefcase"},
            "/briefcase/path/to/file",
        ),
        # Multiple references in a single path are converted
        (
            "/unmodified/path:/base/bundle/path/to/file:/base/briefcase/path/to/other/file",
            {"/base/bundle": "/app", "/base/briefcase": "/briefcase"},
            "/unmodified/path:/app/path/to/file:/briefcase/path/to/other/file",
        ),
        # path_map supports Path objects
        (
            "/unmodified/path:/base/bundle/path/to/file:/base/briefcase/path/to/other/file",
            {
                PurePosixPath("/base/bundle"): Path("/app"),
                Path("/base/briefcase"): PurePosixPath("/briefcase"),
            },
            "/unmodified/path:/app/path/to/file:/briefcase/path/to/other/file",
        ),
    ],
)
def test_dockerize_path(
    mock_docker,
    original,
    path_map,
    dockerized,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr("sys.executable", "/path/to/python")

    converted_path = mock_docker.dockerize_path(
        original,
        path_map=path_map,
    )

    assert converted_path == dockerized
