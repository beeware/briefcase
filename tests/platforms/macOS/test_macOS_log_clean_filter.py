import pytest

from briefcase.platforms.macOS import macOS_log_clean_filter


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
            'AND senderImagePath ENDSWITH "-iphonesimulator.so")"',
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
        # macOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.so) Hello World!",
            ("Hello World!", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.so) Hello World!",
            ("Hello World!", True),
        ),
        # Empty macOS App log
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-312-iphonesimulator.so) ",
            ("", True),
        ),
        (
            "2022-11-14 13:21:15.341 Df My App[59972:780a15] (_ctypes.cpython-38-iphonesimulator.so) ",
            ("", True),
        ),
        # Unknown content
        (
            "This doesn't match the regex",
            ("This doesn't match the regex", False),
        ),
    ],
)
def test_filter(original, filtered):
    assert macOS_log_clean_filter(original) == filtered
