import errno
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.web.static import (
    HTTPHandler,
    LocalHTTPServer,
    StaticWebRunCommand,
)


# OSError doesn't expose errno in the constructor; create some
# custom exceptions that mock common connection errors.
class ErrnoError(OSError):
    def __init__(self, errno):
        super().__init__()
        self.errno = errno


@pytest.fixture
def run_command(tmp_path):
    command = StaticWebRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.data_path = tmp_path / "briefcase"
    return command


def test_default_options(run_command):
    """The default options are as expected."""
    options, overrides = run_command.parse_options([])

    assert options == {
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "update_support": False,
        "update_stub": False,
        "no_update": False,
        "test_mode": False,
        "passthrough": [],
        "host": "localhost",
        "port": 8080,
        "open_browser": True,
    }
    assert overrides == {}


def test_options(run_command):
    """The extra options can be parsed."""
    options, overrides = run_command.parse_options(
        ["--host", "myhost", "--port", "1234", "--no-browser"]
    )

    assert options == {
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "update_support": False,
        "update_stub": False,
        "no_update": False,
        "test_mode": False,
        "passthrough": [],
        "host": "myhost",
        "port": 1234,
        "open_browser": False,
    }
    assert overrides == {}


def test_run(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server."""
    # Mock server creation
    mock_server_init = mock.MagicMock(spec_set=HTTPServer)
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "8080")
    LocalHTTPServer.socket = socket

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(
        first_app_built,
        test_mode=False,
        passthrough=[],
        host="localhost",
        port=8080,
        open_browser=True,
    )

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://127.0.0.1:8080")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_shutdown.assert_called_once_with()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


@pytest.mark.parametrize(
    "exception",
    [
        ErrnoError(errno.EADDRINUSE),
        ErrnoError(errno.ENOSR),
    ],
)
def test_run_with_fallback_port(
    monkeypatch,
    run_command,
    first_app_built,
    exception,
    capsys,
):
    """A static web app can be launched as a server even when the requested port is
    already in use."""
    # Mock server creation that first errors on port, then connects with port 0
    mock_server_init = mock.MagicMock(side_effect=[exception, HTTPServer])
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    # This value has been auto-selected by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "12345")
    LocalHTTPServer.socket = socket

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(
        first_app_built,
        test_mode=False,
        passthrough=[],
        host="localhost",
        port=8080,
        open_browser=True,
    )

    # User is warned a system-allocated port is being used
    assert "Using a system-allocated port since port 8080" in capsys.readouterr().out

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://127.0.0.1:12345")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_shutdown.assert_called_once_with()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


def test_run_with_args(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server; passthrough args will be
    ignored."""
    # Mock server creation
    mock_server_init = mock.MagicMock(spec_set=HTTPServer)
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "8080")
    LocalHTTPServer.socket = socket

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(
        first_app_built,
        test_mode=False,
        passthrough=["foo", "--bar"],
        host="localhost",
        port=8080,
        open_browser=True,
    )

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://127.0.0.1:8080")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shutdown.
    mock_shutdown.assert_called_once_with()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


@pytest.mark.parametrize(
    "host, port, exception, message",
    [
        (
            "localhost",
            80,
            PermissionError(),
            r"Try using a port > 1023\.",
        ),
        (
            "localhost",
            8080,
            PermissionError(),
            r"Did you specify a valid host and port\?",
        ),
        (
            "999.999.999.999",
            8080,
            ErrnoError(errno.EADDRNOTAVAIL),
            r"999.999.999.999 is not a valid hostname.",
        ),
        (
            "999.999.999.999",
            8080,
            ErrnoError(errno.ENOSTR),
            r"999.999.999.999 is not a valid hostname.",
        ),
        (
            "localhost",
            8080,
            OSError("Unknown error"),
            r"Unknown error",
        ),
        (
            "localhost",
            99999,
            OverflowError(),
            r"Port must be in the range 0-65535.",
        ),
    ],
)
def test_cleanup_server_error(
    monkeypatch,
    run_command,
    first_app_built,
    host,
    port,
    exception,
    message,
):
    """If the server raises an error, it is cleaned up."""
    # Mock server creation, raising an error.
    mock_server_init = mock.MagicMock(side_effect=exception)
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock server execution
    mock_serve_forever = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app; an error is raised
    with pytest.raises(BriefcaseCommandError, match=message):
        run_command.run_app(
            first_app_built,
            test_mode=False,
            passthrough=[],
            host=host,
            port=port,
            open_browser=True,
        )

    # The browser was not opened
    mock_open_new_tab.assert_not_called()

    # The server was not started
    mock_serve_forever.assert_not_called()

    # The webserver was never started, so it wasn't shut down either.
    mock_shutdown.assert_not_called()
    mock_server_close.assert_not_called()


def test_cleanup_runtime_server_error(monkeypatch, run_command, first_app_built):
    """If the server raises an error at runtime, it is cleaned up."""
    # Mock server creation, raising an error due to an already used port.
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "8080")
    LocalHTTPServer.socket = socket

    # Mock server execution
    mock_serve_forever = mock.MagicMock(side_effect=ValueError())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app; it raises an error
    with pytest.raises(ValueError):
        run_command.run_app(
            first_app_built,
            test_mode=False,
            passthrough=[],
            host="localhost",
            port=8080,
            open_browser=True,
        )

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://127.0.0.1:8080")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The server crashed, so it won't need to be shut down
    mock_shutdown.assert_not_called()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


def test_run_without_browser(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server."""
    # Mock server creation
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "8080")
    LocalHTTPServer.socket = socket

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app
    run_command.run_app(
        first_app_built,
        test_mode=False,
        passthrough=[],
        host="localhost",
        port=8080,
        open_browser=False,
    )

    # The browser was not opened
    mock_open_new_tab.assert_not_called()

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shut down.
    mock_shutdown.assert_called_once_with()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


def test_run_autoselect_port(monkeypatch, run_command, first_app_built):
    """A static web app can be launched as a server."""
    # Mock server creation
    mock_server_init = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "__init__", mock_server_init)

    # Mock the socket name returned by the server.
    # This value has been auto-selected by the server.
    socket = mock.MagicMock()
    socket.getsockname.return_value = ("127.0.0.1", "12345")
    LocalHTTPServer.socket = socket

    # Mock server execution, raising a user exit.
    mock_serve_forever = mock.MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(HTTPServer, "serve_forever", mock_serve_forever)

    # Mock shutdown
    mock_shutdown = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "shutdown", mock_shutdown)

    # Mock server close
    mock_server_close = mock.MagicMock()
    monkeypatch.setattr(HTTPServer, "server_close", mock_server_close)

    # Mock the webbrowser
    mock_open_new_tab = mock.MagicMock()
    monkeypatch.setattr(webbrowser, "open_new_tab", mock_open_new_tab)

    # Run the app on an autoselected port
    run_command.run_app(
        first_app_built,
        test_mode=False,
        passthrough=[],
        host="localhost",
        port=0,
        open_browser=True,
    )

    # The browser was opened
    mock_open_new_tab.assert_called_once_with("http://127.0.0.1:12345")

    # The server was started
    mock_serve_forever.assert_called_once_with()

    # The webserver was shut down.
    mock_shutdown.assert_called_once_with()

    # The webserver was closed.
    mock_server_close.assert_called_once_with()


def test_served_paths(monkeypatch, tmp_path):
    """URLs are converted into paths in the project www folder."""
    # Mock server creation
    mock_server_init = mock.MagicMock(return_value=None)
    monkeypatch.setattr(SimpleHTTPRequestHandler, "__init__", mock_server_init)

    # Create a handler instance.
    request = mock.MagicMock()
    server = mock.MagicMock()
    handler = HTTPHandler(request, ("localhost", 8080), server)

    # We need some properties that are set on the handler instance
    # by the superclass; force set them here for test purposes.
    handler.server = server
    handler.server.base_path = tmp_path / "base_path"

    # Invoke this as a static method because we don't want to
    # instantiate a full server just to verify that URL rewriting works.
    assert handler.translate_path("/static/css/briefcase.css") == str(
        tmp_path / "base_path/static/css/briefcase.css"
    )


def test_cache_headers(monkeypatch, tmp_path):
    """Server sets no-cache headers."""
    # Mock server creation
    mock_server_init = mock.MagicMock(return_value=None)
    monkeypatch.setattr(SimpleHTTPRequestHandler, "__init__", mock_server_init)

    # Mock end_headers on the base class
    mock_end_headers = mock.MagicMock()
    monkeypatch.setattr(SimpleHTTPRequestHandler, "end_headers", mock_end_headers)

    # Create a handler instance.
    request = mock.MagicMock()
    server = mock.MagicMock()
    handler = HTTPHandler(request, ("localhost", 8080), server)

    # We need some properties that are set on the handler instance
    # by the superclass; force set them here for test purposes.
    handler.request_version = "HTTP/1.1"

    # Invoke end_headers()
    handler.end_headers()

    # end_headers was invoked on the base class...
    mock_end_headers.assert_called_once_with()

    # ...but the custom handler added cache control headers.
    assert handler._headers_buffer == [
        b"Cache-Control: no-cache, no-store, must-revalidate\r\n",
        b"Pragma: no-cache\r\n",
        b"Expires: 0\r\n",
    ]


def test_log_requests_to_logger(monkeypatch):
    """The request handler logs messages to the server's logger."""
    monkeypatch.setattr(
        SimpleHTTPRequestHandler, "handle", mock.Mock(return_value=None)
    )
    server = mock.MagicMock()
    handler = HTTPHandler(mock.MagicMock(), ("localhost", 8080), server)
    handler.log_date_time_string = mock.Mock(return_value="now")
    handler.log_message("hello\033")
    server.logger.info.assert_called_once_with("localhost - - [now] hello\\x1b")


def test_test_mode(run_command, first_app_built):
    """Test mode raises an error (at least for now)."""
    # Run the app
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase can't run web apps in test mode.",
    ):
        run_command.run_app(
            first_app_built,
            test_mode=True,
            passthrough=[],
            host="localhost",
            port=8080,
            open_browser=True,
        )
