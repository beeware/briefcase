import webbrowser
from http.server import HTTPServer
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import HTTPHandler, StaticWebRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = StaticWebRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.data_path = tmp_path / "briefcase"
    return command


def test_default_options(run_command):
    """The default options are as expected."""
    options = run_command.parse_options([])

    assert options == {
        "appname": None,
        "update": False,
        "host": "localhost",
        "port": 8080,
        "open_browser": True,
    }


def test_options(run_command):
    """The extra options can be parsed."""
    options = run_command.parse_options(
        ["--host", "myhost", "--port", "1234", "--no-browser"]
    )

    assert options == {
        "appname": None,
        "update": False,
        "host": "myhost",
        "port": 1234,
        "open_browser": False,
    }


def test_run(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server."""
    # Mock server creation
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock server shutdown
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(first_app_built, "localhost", 8080, open_browser=True)

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://localhost:8080")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_server_close.assert_called_once_with()


def test_cleanup_server_error(monkeypatch, run_command, first_app_built):
    """If the server raises an error, it is cleaned up."""
    # Mock server creation, raising an error due to an already used port.
    mock_server_init = mock.MagicMock(side_effect=OSError())
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock server execution
    mock_serve_forever = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock server shutdown
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app; an error is raised
    with pytest.raises(OSError):
        run_command.run_app(first_app_built, "localhost", 8080, open_browser=True)

    # The browser was not opened
    mock_open_new_tab.assert_not_called()

    # The server was not started
    mock_serve_forever.assert_not_called()

    # The webserver was never started, so it wasn't shut down either.
    mock_server_close.assert_not_called()


def test_cleanup_runtime_server_error(monkeypatch, run_command, first_app_built):
    """If the server raises an error at runtime, it is cleaned up."""
    # Mock server creation, raising an error due to an already used port.
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock server execution
    mock_serve_forever = mock.MagicMock(side_effect=ValueError())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock server shutdown
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app; it raises an error
    with pytest.raises(ValueError):
        run_command.run_app(first_app_built, "localhost", 8080, open_browser=True)

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://localhost:8080")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_server_close.assert_called_once_with()


def test_run_without_browser(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server."""
    # Mock server creation
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock server shutdown
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(first_app_built, "localhost", 8080, open_browser=False)

    # The browser was not opened
    mock_open_new_tab.assert_not_called()

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_server_close.assert_called_once_with()


def test_served_paths(tmp_path):
    "URLs are converted into paths in the project www folder"
    # Mock a handler with a server working on a known path.
    handler = mock.MagicMock()
    handler.server.base_path = tmp_path / "base_path"

    # Invoke this as a static method because we don't want to
    # instantiate a full server just to verify that URL rewriting works.
    assert HTTPHandler.translate_path(handler, "/static/css/briefcase.css") == str(
        tmp_path / "base_path" / "static" / "css" / "briefcase.css"
    )
