import pytest

from briefcase.platforms.android.gradle import android_log_clean_filter


@pytest.mark.parametrize(
    "original, filtered",
    [
        # Start of app log
        (
            "--------- beginning of main",
            ("--------- beginning of main", False),
        ),
        # System messages log
        (
            "D/libEGL  : loaded /vendor/lib64/egl/libEGL_emulation.so",
            (
                "loaded /vendor/lib64/egl/libEGL_emulation.so",
                False,
            ),
        ),
        (
            "\x1b[32mD/libEGL  : loaded /vendor/lib64/egl/libEGL_emulation.so\x1b[0m",
            (
                "loaded /vendor/lib64/egl/libEGL_emulation.so",
                False,
            ),
        ),
        (
            "D/stdio   : Could not find platform independent libraries <prefix>",
            ("Could not find platform independent libraries <prefix>", False),
        ),
        (
            "D/MainActivity: onStart() start",
            ("onStart() start", False),
        ),
        (
            "\x1b[32mD/MainActivity: onStart() start\x1b[0m",
            ("onStart() start", False),
        ),
        # Python App messages
        (
            "I/python.stdout: Python app launched & stored in Android Activity class",
            ("Python app launched & stored in Android Activity class", True),
        ),
        (
            "\x1b[32mI/python.stdout: Python app launched & stored in Android Activity class\x1b[0m",
            ("Python app launched & stored in Android Activity class", True),
        ),
        (
            "I/python.stdout: ",
            ("", True),
        ),
        (
            "\x1b[32mI/python.stdout: \x1b[0m",
            ("", True),
        ),
        (
            "\x1b[32m\x1b[98mI/python.stdout: \x1b[32m\x1b[0m",
            ("", True),
        ),
        (
            "\x1b[32m\x1b[98mI/python.stdout: this is colored output\x1b[32m\x1b[0m",
            ("this is colored output", True),
        ),
        (
            "I/python.stderr: test_case (tests.foobar.test_other.TestOtherMethods)",
            ("test_case (tests.foobar.test_other.TestOtherMethods)", True),
        ),
        (
            "\x1b[32mI/python.stderr: test_case (tests.foobar.test_other.TestOtherMethods)\x1b[0m",
            ("test_case (tests.foobar.test_other.TestOtherMethods)", True),
        ),
        (
            "I/python.stderr: ",
            ("", True),
        ),
        (
            "\x1b[32mI/python.stderr: \x1b[0m",
            ("", True),
        ),
        # Unknown content
        (
            "This doesn't match the regex",
            ("This doesn't match the regex", False),
        ),
        (
            "\x1b[33mThis doesn't match the regex\x1b[33m",
            ("\x1b[33mThis doesn't match the regex\x1b[33m", False),
        ),
    ],
)
def test_filter(original, filtered):
    assert android_log_clean_filter(original) == filtered
