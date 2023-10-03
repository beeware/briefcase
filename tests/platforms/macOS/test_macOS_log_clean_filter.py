import pytest

from briefcase.platforms.macOS.filters import macOS_log_clean_filter


@pytest.mark.parametrize(
    "original, filtered",
    [
        # macOS Logging preamble
        (
            "Filtering the log data using "
            '"senderImagePath == "/path/to/My App.app/Contents/MacOS/My App" '
            'OR (processImagePath == "/path/to/My App.app/Contents/MacOS/My App" '
            'AND senderImagePath == "/usr/lib/libffi.dylib")"',
            None,
        ),
        (
            "Timestamp               Ty Process[PID:TID]",
            None,
        ),
        # iOS Logging preamble
        (
            "Error from getpwuid_r: 0 (Undefined error: 0)",
            None,
        ),
        (
            'Filtering the log data using "senderImagePath ENDSWITH "/Toga Test!" '
            'OR (processImagePath ENDSWITH "/Toga Test!" '
            'AND (senderImagePath ENDSWITH "-iphonesimulator.so" '
            'OR senderImagePath ENDSWITH "-iphonesimulator.dylib"))"',
            None,
        ),
        # Startup log
        (
            "2022-11-14 13:21:14.972 Df My App[59972:780a15] Configure argc/argv...",
            ("Configure argc/argv...", False),
        ),
        # Empty startup log
        (
            "2022-11-14 13:21:14.972 Df My App[59972:780a15] ",
            ("", False),
        ),
        # macOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (libffi.dylib) Hello World!",
            ("Hello World!", True),
        ),
        # Empty macOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (libffi.dylib) ",
            ("", True),
        ),
        # iOS App log (old style .so libraries)
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.so) Hello World!",
            ("Hello World!", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.so) Hello World!",
            ("Hello World!", True),
        ),
        # iOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.dylib) Hello World!",
            ("Hello World!", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.dylib) Hello World!",
            ("Hello World!", True),
        ),
        # Empty iOS App log (old style .so binaries)
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.so) ",
            ("", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.so) ",
            ("", True),
        ),
        # Empty iOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.dylib) ",
            ("", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.dylib) ",
            ("", True),
        ),
        # Unknown content
        (
            "This doesn't match the regex",
            ("This doesn't match the regex", False),
        ),
        # Log content that contains square brackets
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (libffi.dylib) Test [1/5] ... OK",
            ("Test [1/5] ... OK", True),
        ),
        # Log content that contains `.so`
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.so) "
            "A problem (foo.so) try to avoid it",
            ("A problem (foo.so) try to avoid it", True),
        ),
        # Log content that contains `.dylib`
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.dylib) "
            "A problem (foo.dylib) try to avoid it",
            ("A problem (foo.dylib) try to avoid it", True),
        ),
    ],
)
def test_filter(original, filtered):
    assert macOS_log_clean_filter(original) == filtered
