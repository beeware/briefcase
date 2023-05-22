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
            "D/stdio   : Could not find platform independent libraries <prefix>",
            ("Could not find platform independent libraries <prefix>", False),
        ),
        (
            "D/MainActivity: onStart() start",
            ("onStart() start", False),
        ),
        # Python App messages
        (
            "I/python.stdout: Python app launched & stored in Android Activity class",
            ("Python app launched & stored in Android Activity class", True),
        ),
        (
            "I/python.stdout: ",
            ("", True),
        ),
        (
            "I/python.stderr: test_case (tests.foobar.test_other.TestOtherMethods)",
            ("test_case (tests.foobar.test_other.TestOtherMethods)", True),
        ),
        (
            "I/python.stderr: ",
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
    assert android_log_clean_filter(original) == filtered
