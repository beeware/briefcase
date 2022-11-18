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
            "11-16 14:32:57.866  4041  4041 D libEGL  : loaded /vendor/lib64/egl/libEGL_emulation.so",
            (
                "loaded /vendor/lib64/egl/libEGL_emulation.so",
                False,
            ),
        ),
        (
            "11-16 14:32:57.967  4041  4067 D stdio   : Could not find platform independent libraries <prefix>",
            ("Could not find platform independent libraries <prefix>", False),
        ),
        (
            "11-16 14:32:58.218  4041  4041 D MainActivity: onStart() start",
            ("onStart() start", False),
        ),
        # Python App messages
        (
            "11-16 14:32:58.195  4041  4041 I python.stdout: Python app launched & stored in Android Activity class",
            ("Python app launched & stored in Android Activity class", True),
        ),
        (
            "11-16 14:32:58.195  4041  4041 I python.stdout: ",
            ("", True),
        ),
        (
            "11-16 14:32:58.195  4041  4041 I python.stderr: test_case (tests.foobar.test_other.TestOtherMethods)",
            ("test_case (tests.foobar.test_other.TestOtherMethods)", True),
        ),
        (
            "11-16 14:32:58.195  4041  4041 I python.stderr: ",
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
