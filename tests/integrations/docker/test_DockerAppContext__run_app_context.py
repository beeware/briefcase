from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_run_app_context(mock_tools, my_app):
    """Run app context calls X11 passthrough and returns the keywords."""
    # Mock X11 passthrough manager with the null manager
    mock_tools.docker.x11_passthrough = MagicMock(wraps=nullcontext)

    in_kwargs = {"keyword_one": "val1", "keyword_two": "val2"}

    with mock_tools[my_app].app_context.run_app_context(in_kwargs) as kwargs:
        assert kwargs == in_kwargs

    mock_tools.docker.x11_passthrough.assert_called_once_with(in_kwargs)
