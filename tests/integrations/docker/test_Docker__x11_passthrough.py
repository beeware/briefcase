import socket
import subprocess
import sys
from pathlib import Path, PosixPath, PurePosixPath
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import XauthDatabaseCreationFailure

XAUTH_LIST_RET_1 = (
    "0000 0004 7f000101 0002 3132 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 1b185a208e4600e717f3b8903fc35141\n"
    "0000 0004 7f000101 0002 3130 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 da9667aa96def95dfa44e01f1b13e55b\n"
    "0100 0006 70692d372d35 0002 3133 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 72e93a771996c40f8465a7aa9add67e0\n"
    "0100 0006 70692d372d35 0002 3134 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 870c9e1d92ee663f93955d7fc27a3641\n"
    "0100 0006 70692d372d35 0002 3135 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 17d837a0890cdf5588bd793ef3410357\n"
    "0100 0006 70692d372d35 0002 3132 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 cb329aff1071b8bd66f24af31c8460cc\n"
    "0100 0006 70692d372d35 0002 3130 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 187dcffa78c868e5c5f67b6640c299f5\n"
    "0100 0006 70692d372d35 0002 3131 0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 f22b85acf66a5819f5e15c2ac5af25b2"
)

XAUTH_LIST_RET_2 = (
    "0100 0007 6a757069746572 0000  0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 fa4b61837675f1581427e0c937701439\n"
    "ffff 0007 6a757069746572 0000  0012 "
    "4d49542d4d414749432d434f4f4b49452d31 0010 fa4b61837675f1581427e0c937701439"
)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "display_num, expected_socket_path",
    [("1", "/tmp/.X11-unix/X1"), (2, "/tmp/.X11-unix/X2")],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_display_socket_path(mock_tools, display_num, expected_socket_path):
    """Path for socket is returned for X11 display."""
    socket_path = mock_tools.docker._x11_display_unix_socket_path(display_num)
    assert socket_path == PosixPath(expected_socket_path)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "path_is_socket_outcome, expected_outcome",
    [(True, True), (OSError, False), (False, False)],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_is_display_socket(mock_tools, path_is_socket_outcome, expected_outcome):
    """X11 display UNIX socket is validated for X display number."""
    # Mock the Path for the X display socket
    mock_socket_path = MagicMock(spec_set=PosixPath)
    mock_socket_path.is_socket.side_effect = [path_is_socket_outcome]
    mock_tools.docker._x11_display_unix_socket_path = MagicMock(
        return_value=mock_socket_path
    )

    assert mock_tools.docker._x11_is_display_unix(1) is expected_outcome


@pytest.mark.parametrize(
    "connect_ret, display_num, connect_port, expected_outcome",
    [
        (0, 0, 6000, True),
        (0, 100, 6100, True),
        (1, 42, 6042, False),
        (OSError, 1, 6001, False),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_is_display_tcp(
    mock_tools,
    connect_ret,
    display_num,
    connect_port,
    expected_outcome,
    monkeypatch,
):
    """X11 display TCP socket is validated for X display number."""
    # Mock the socket manager
    mock_sock = MagicMock()
    mock_sock.connect_ex.side_effect = [connect_ret]
    mock_socket_manager = MagicMock()
    mock_socket_manager.__enter__.return_value = mock_sock
    mock_socket = MagicMock(return_value=mock_socket_manager)
    monkeypatch.setattr("socket.socket", mock_socket)

    assert mock_tools.docker._x11_is_display_tcp(display_num) is expected_outcome

    # Socket connection timeout is set
    mock_sock.settimeout.assert_called_once_with(3)
    # Connection type for socket is correct
    mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    # Connection attempt to the proper port
    mock_sock.connect_ex.assert_called_once_with(("localhost", connect_port))


@pytest.mark.parametrize(
    "is_socket_outcomes, is_tcp_outcomes, expected_display_num",
    [
        ([False], [False], 50),
        # Due to short-circuiting, only the first iterator is consumed if it returns False
        ([True, False], [False], 51),
        ([True, True, False, True, False], [False, False, False], 52),
        ([True] * 248 + [False, False], [True, False], 299),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_allocate_display_success(
    mock_tools,
    is_socket_outcomes,
    is_tcp_outcomes,
    expected_display_num,
):
    """Allocating an X display number succeeds for a qualifying candidate."""
    # Mock X display socket checks
    mock_tools.docker._x11_is_display_unix = MagicMock(side_effect=is_socket_outcomes)
    mock_tools.docker._x11_is_display_tcp = MagicMock(side_effect=is_tcp_outcomes)

    assert mock_tools.docker._x11_allocate_display() == expected_display_num


@pytest.mark.parametrize(
    "is_socket_outcomes, is_tcp_outcomes",
    [
        ([True] * 250, [False] * 250),
        ([False] * 250, [True] * 250),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_allocate_display_failure(mock_tools, is_socket_outcomes, is_tcp_outcomes):
    """Allocating an X display number fails if the range is exhausted."""
    # Mock X display socket checks
    mock_tools.docker._x11_is_display_unix = MagicMock(side_effect=is_socket_outcomes)
    mock_tools.docker._x11_is_display_tcp = MagicMock(side_effect=is_tcp_outcomes)

    with pytest.raises(BriefcaseCommandError, match="Failed to allocate X11 display"):
        mock_tools.docker._x11_allocate_display()


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "display_number, expected_xauth_path",
    [
        (1, Path.cwd() / "build/.briefcase.docker.xauth.1"),
        (50, Path.cwd() / "build/.briefcase.docker.xauth.50"),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_proxy_display_xauth_file_path(
    mock_tools,
    display_number,
    expected_xauth_path,
):
    """The xauth database file path is generated correctly for the display number."""
    xauth_path = mock_tools.docker._x11_proxy_display_xauth_file_path(display_number)
    assert xauth_path == PosixPath(expected_xauth_path)


@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_missing_xauth_bin(mock_tools, tmp_path):
    """When the xauth program cannot be found, an error is raised."""
    mock_tools.shutil.which.return_value = ""

    with pytest.raises(BriefcaseCommandError, match="Install xauth to run an app"):
        mock_tools.docker._x11_write_xauth_file(
            DISPLAY=":66",
            xauth_file_path=tmp_path / "test_xauth_file",
            target_display_num=42,
        )


@pytest.mark.parametrize(
    "xauth_nlist_outcome",
    [
        subprocess.CalledProcessError(
            returncode=1, cmd=["xauth", "-i", "nlist", ":66"]
        ),
        "not found",
        "",
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_get_cookie_fails(mock_tools, xauth_nlist_outcome, tmp_path):
    """If the attempt to retrieve the current display's cookie fails, an error is
    raised."""

    mock_tools.subprocess._subprocess.check_output.side_effect = [xauth_nlist_outcome]

    with pytest.raises(
        XauthDatabaseCreationFailure, match="Failed to retrieve xauth cookie"
    ):
        mock_tools.docker._x11_write_xauth_file(
            DISPLAY=":66",
            xauth_file_path=tmp_path / "test_xauth_file",
            target_display_num=42,
        )


@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_add_new_xauth_fails(mock_tools, tmp_path):
    """If the attempt to retrieve the current display's cookie fails, an error is
    raised."""

    mock_tools.subprocess._subprocess.check_output.side_effect = [
        # xauth -i nlist :66
        XAUTH_LIST_RET_1,
        subprocess.CalledProcessError(
            returncode=1,
            cmd=[
                "xauth",
                "-i",
                "-f",
                str(tmp_path / "test_xauth_file"),
                "add",
                ":66",
                "MIT-MAGIC-COOKIE-1",
                "cookie",
            ],
        ),
    ]

    with pytest.raises(
        XauthDatabaseCreationFailure,
        match="Failed to add a xauth entry for existing cookie",
    ):
        mock_tools.docker._x11_write_xauth_file(
            DISPLAY=":66",
            xauth_file_path=tmp_path / "test_xauth_file",
            target_display_num=42,
        )


@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_retrieve_xauth_fails(mock_tools, tmp_path):
    """If the attempt to retrieve the target display's xauth list, an error is
    raised."""

    mock_tools.subprocess._subprocess.check_output.side_effect = [
        # xauth -i nlist :66
        XAUTH_LIST_RET_1,
        # xauth -i -f "xauth_file_path" add "MIT-MAGIC-COOKIE-1" <cookie>
        "xauth add success",
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xauth", "-i", "-f", str(tmp_path / "test_xauth_file"), "nlist"],
        ),
    ]

    with pytest.raises(
        XauthDatabaseCreationFailure, match="Failed to retrieve xauth list"
    ):
        mock_tools.docker._x11_write_xauth_file(
            DISPLAY=":66",
            xauth_file_path=tmp_path / "test_xauth_file",
            target_display_num=42,
        )


@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_merge_xauth_fails(mock_tools, tmp_path):
    """If the attempt to retrieve the target display's xauth list, an error is
    raised."""

    mock_tools.subprocess._subprocess.check_output.side_effect = [
        # xauth -i nlist :66
        XAUTH_LIST_RET_1,
        # xauth -i -f "xauth_file_path" add "MIT-MAGIC-COOKIE-1" <cookie>
        "xauth add success",
        # xauth -i -f "xauth_file_path" nlist
        XAUTH_LIST_RET_2,
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xauth", "-f", str(tmp_path / "test_xauth_file"), "nmerge", "-"],
        ),
    ]

    with pytest.raises(
        XauthDatabaseCreationFailure,
        match="Failed to merge xauth updates for FamilyWild hostname",
    ):
        mock_tools.docker._x11_write_xauth_file(
            DISPLAY=":66",
            xauth_file_path=tmp_path / "test_xauth_file",
            target_display_num=42,
        )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_write_xauth_success(mock_tools, tmp_path, sub_check_output_kw):
    """The attempt to write the xauth database for the target display succeeds."""

    mock_tools.subprocess._subprocess.check_output.side_effect = [
        # xauth -i nlist :66
        XAUTH_LIST_RET_1,
        # xauth -i -f "xauth_file_path" add "MIT-MAGIC-COOKIE-1" <cookie>
        "xauth add success",
        # xauth -i -f "xauth_file_path" nlist
        XAUTH_LIST_RET_2,
        # xauth -i -f "xauth_file_path" nmerge -
        "xauth nmerge success",
    ]

    mock_tools.docker._x11_write_xauth_file(
        DISPLAY=":66",
        xauth_file_path=tmp_path / "test_xauth_file",
        target_display_num=42,
    )

    mock_tools.subprocess._subprocess.check_output.assert_has_calls(
        [
            call(["xauth", "-i", "nlist", ":66"], **sub_check_output_kw),
            call(
                [
                    "xauth",
                    "-i",
                    "-f",
                    f"{tmp_path}/test_xauth_file",
                    "add",
                    ":42",
                    "MIT-MAGIC-COOKIE-1",
                    "1b185a208e4600e717f3b8903fc35141",
                ],
                **sub_check_output_kw,
            ),
            call(
                [
                    "xauth",
                    "-i",
                    "-f",
                    f"{tmp_path}/test_xauth_file",
                    "nlist",
                ],
                **sub_check_output_kw,
            ),
            call(
                [
                    "xauth",
                    "-i",
                    "-f",
                    f"{tmp_path}/test_xauth_file",
                    "nmerge",
                    "-",
                ],
                input=(
                    "ffff 0007 6a757069746572 0000  0012 4d49542d4d414749432d434f4f4b49452d31 "
                    "0010 fa4b61837675f1581427e0c937701439\n"
                    "ffff 0007 6a757069746572 0000  0012 4d49542d4d414749432d434f4f4b49452d31 "
                    "0010 fa4b61837675f1581427e0c937701439"
                ),
                **sub_check_output_kw,
            ),
        ],
    )


@pytest.mark.usefixtures("mock_docker")
def test_x11_tcp_proxy_missing_socat_bin(mock_tools):
    """When the socat program cannot be found, an error is raised."""
    mock_tools.shutil.which.return_value = ""

    with pytest.raises(
        BriefcaseCommandError,
        match="Install socat to run an app for a targeted Linux distribution",
    ):
        mock_tools.docker._x11_tcp_proxy(DISPLAY=":66")


@pytest.mark.parametrize("DISPLAY", [None, "", "host;42.0", 42, "42"])
@pytest.mark.usefixtures("mock_docker")
def test_x11_tcp_proxy_invalid_DISPLAY(mock_tools, DISPLAY):
    """When the DISPLAY environment variable is invalid, an error is raised."""
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Unsupported value for environment variable DISPLAY: '{DISPLAY}'",
    ):
        mock_tools.docker._x11_tcp_proxy(DISPLAY=DISPLAY)


@pytest.mark.usefixtures("mock_docker")
def test_x11_tcp_proxy_unknown_display_socket(mock_tools):
    """When a socket for the current display cannot be found, an error is raised."""
    # Mock target display allocation
    mock_tools.docker._x11_allocate_display = MagicMock(return_value=42)
    # Mock current display sockets cannot be found
    mock_tools.docker._x11_is_display_tcp = MagicMock(return_value=False)
    mock_tools.docker._x11_is_display_unix = MagicMock(return_value=False)

    with pytest.raises(
        BriefcaseCommandError,
        match="Cannot find X11 display for ':42'",
    ):
        mock_tools.docker._x11_tcp_proxy(DISPLAY=":42")


@pytest.mark.parametrize(
    "is_unix, is_tcp, current_display_num, target_display_num, connect_def",
    [
        (False, True, 142, 42, "TCP:localhost:{tcp_port}"),
        (False, True, 166, 66, "TCP:localhost:{tcp_port}"),
        (True, True, 166, 66, "TCP:localhost:{tcp_port}"),
        (True, False, 142, 42, "UNIX-CONNECT:/tmp/.X11-unix/X{display_num}"),
        (True, False, 166, 66, "UNIX-CONNECT:/tmp/.X11-unix/X{display_num}"),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_tcp_proxy_create_success(
    mock_tools,
    is_unix,
    is_tcp,
    current_display_num,
    target_display_num,
    connect_def,
    sub_kw,
):
    """When current display has a socket, the proxy is to that TCP socket."""
    # Mock target display allocation
    mock_tools.docker._x11_allocate_display = MagicMock(return_value=target_display_num)
    # Mock current display sockets cannot be found
    mock_tools.docker._x11_is_display_tcp = MagicMock(return_value=is_tcp)
    mock_tools.docker._x11_is_display_unix = MagicMock(return_value=is_unix)
    # Mock proxy process
    mock_proxy_popen = MagicMock(spec_set=subprocess.Popen)
    mock_tools.subprocess._subprocess.Popen.return_value = mock_proxy_popen

    proxy_popen, proxy_display_num = mock_tools.docker._x11_tcp_proxy(
        DISPLAY=f"host:{current_display_num}.0"
    )

    # Proxy and spoofed target display are returned
    assert proxy_popen is mock_proxy_popen
    assert proxy_display_num == target_display_num

    # Proxy created properly
    mock_tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "socat",
            f"TCP-LISTEN:{6000 + target_display_num},reuseaddr,fork,bind=0.0.0.0",
            connect_def.format(
                tcp_port=6000 + current_display_num,
                display_num=current_display_num,
            ),
        ],
        **sub_kw,
    )


@pytest.mark.parametrize("DISPLAY", [None, ""])
@pytest.mark.usefixtures("mock_docker")
def test_x11_passthrough_missing_DISPLAY(mock_tools, DISPLAY):
    """If the DISPLAY variable is not set, an error is raised."""
    # Mock DISPLAY environment variable
    mock_tools.os.getenv.return_value = DISPLAY

    with pytest.raises(
        BriefcaseCommandError,
        match="The DISPLAY environment variable must be set to run an app in Docker",
    ):
        with mock_tools.docker.x11_passthrough({}):
            pass


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_passthrough_fails(mock_tools):
    """Cleanup runs even if passthrough fails."""
    # Mock DISPLAY environment variable
    mock_tools.os.getenv.return_value = "host:42.0"
    # Mock Subprocess.cleanup()
    mock_tools.subprocess.cleanup = MagicMock()
    # Mock the proxy
    mock_proxy_popen = MagicMock(spec_set=subprocess.Popen)
    mock_tools.docker._x11_tcp_proxy = MagicMock(return_value=(mock_proxy_popen, 66))
    # Mock xauth database file path
    mock_xauth_file_path = MagicMock(spec_set=PosixPath)
    mock_tools.docker._x11_proxy_display_xauth_file_path = MagicMock(
        return_value=mock_xauth_file_path
    )
    # Mock the xauth database file write failing (beyond what's expected)
    mock_tools.docker._x11_write_xauth_file = MagicMock(
        side_effect=OSError("write failed")
    )

    with pytest.raises(OSError, match="write failed"):
        with mock_tools.docker.x11_passthrough({}):
            pass

    # Proxy cleanup ran
    mock_tools.subprocess.cleanup.assert_called_once_with(
        "X display proxy", mock_proxy_popen
    )
    mock_xauth_file_path.unlink.assert_called_once_with(missing_ok=True)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "in_kwargs, out_kwargs",
    [
        (
            {
                "input1": "value1",
                "input2": "value2",
                "env": {"existing-var": "existing-val"},
                "mounts": [("/outside", "/inside")],
                "add_hosts": [("source", "target")],
            },
            {
                "input1": "value1",
                "input2": "value2",
                "env": {
                    "existing-var": "existing-val",
                    "DISPLAY": "host.docker.internal:66",
                },
                "mounts": [
                    ("/outside", "/inside"),
                ],
                "add_hosts": [
                    ("source", "target"),
                    ("host.docker.internal", "host-gateway"),
                ],
            },
        ),
        (
            {},
            {
                "env": {
                    "DISPLAY": "host.docker.internal:66",
                },
                "add_hosts": [("host.docker.internal", "host-gateway")],
            },
        ),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_passthrough_xauth_fails(mock_tools, in_kwargs, out_kwargs, capsys):
    """Passthrough configuration is successful even if xauth fails and cleanup runs."""
    # Mock DISPLAY environment variable
    mock_tools.os.getenv.return_value = "host:42.0"
    # Mock Subprocess.cleanup()
    mock_tools.subprocess.cleanup = MagicMock()
    # Mock the proxy
    mock_proxy_popen = MagicMock(spec_set=subprocess.Popen)
    mock_tools.docker._x11_tcp_proxy = MagicMock(return_value=(mock_proxy_popen, 66))
    # Mock xauth database file path
    mock_xauth_file_path = MagicMock(spec_set=PosixPath)
    mock_tools.docker._x11_proxy_display_xauth_file_path = MagicMock(
        return_value=mock_xauth_file_path
    )
    # Mock the xauth database file write failing
    mock_tools.docker._x11_write_xauth_file = MagicMock(
        side_effect=XauthDatabaseCreationFailure("write failed")
    )

    with mock_tools.docker.x11_passthrough(in_kwargs) as kwargs:
        assert kwargs == out_kwargs

    # Proxy cleanup ran
    mock_tools.subprocess.cleanup.assert_called_once_with(
        "X display proxy", mock_proxy_popen
    )
    mock_xauth_file_path.unlink.assert_called_once_with(missing_ok=True)

    # User is warned that xauth failed
    assert capsys.readouterr().out == (
        "An X11 authentication database could not be created for the display.\n"
        "\n"
        "Briefcase will proceed, but if access to the display is rejected, this may be why.\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "in_kwargs, out_kwargs",
    [
        (
            {
                "input1": "value1",
                "input2": "value2",
                "env": {"existing-var": "existing-val"},
                "mounts": [("/outside", "/inside")],
                "add_hosts": [("source", "target")],
            },
            {
                "input1": "value1",
                "input2": "value2",
                "env": {
                    "existing-var": "existing-val",
                    "DISPLAY": "host.docker.internal:66",
                    "XAUTHORITY": "<placeholder>",
                },
                "mounts": [
                    ("/outside", "/inside"),
                ],
                "add_hosts": [
                    ("source", "target"),
                    ("host.docker.internal", "host-gateway"),
                ],
            },
        ),
        (
            {},
            {
                "env": {
                    "DISPLAY": "host.docker.internal:66",
                    "XAUTHORITY": "<placeholder>",
                },
                "mounts": [],
                "add_hosts": [("host.docker.internal", "host-gateway")],
            },
        ),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_x11_passthrough_success(mock_tools, in_kwargs, out_kwargs, capsys):
    """Passthrough configuration is successful and cleanup runs."""
    # Mock DISPLAY environment variable
    mock_tools.os.getenv.return_value = "host:42.0"
    # Mock Subprocess.cleanup()
    mock_tools.subprocess.cleanup = MagicMock()
    # Mock the proxy
    mock_proxy_popen = MagicMock(spec_set=subprocess.Popen)
    mock_tools.docker._x11_tcp_proxy = MagicMock(return_value=(mock_proxy_popen, 66))
    # Mock xauth database file path
    mock_xauth_file_path = MagicMock(wraps=PosixPath("/tmp/subdir/xauth_file.db"))
    mock_xauth_file_path.name = "xauth_file.db"
    mock_tools.docker._x11_proxy_display_xauth_file_path = MagicMock(
        return_value=mock_xauth_file_path
    )
    # Mock the xauth database file write
    mock_tools.docker._x11_write_xauth_file = MagicMock()

    # Finish filling out augmented subprocess kwargs
    out_kwargs.setdefault("mounts", []).append(
        (mock_xauth_file_path, PurePosixPath("/tmp/xauth_file.db"))
    )
    out_kwargs.setdefault("env", {})["XAUTHORITY"] = PurePosixPath("/tmp/xauth_file.db")

    with mock_tools.docker.x11_passthrough(subprocess_kwargs=in_kwargs) as kwargs:
        assert kwargs == out_kwargs

    # Proxy cleanup ran
    mock_tools.subprocess.cleanup.assert_called_once_with(
        "X display proxy", mock_proxy_popen
    )
    mock_xauth_file_path.unlink.assert_called_once_with(missing_ok=True)

    # No console output
    assert capsys.readouterr().out == ""
