import pytest

test_title = "ANDROID_HOME and ANDROID_SDK_ROOT are inconsistent"
test_message = """
    The ANDROID_HOME and ANDROID_SDK_ROOT environment variables
    are set to different paths:

        ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
        ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/\
test_warning_banner.py

     Briefcase will ignore ANDROID_SDK_ROOT and only use the path
    specified by ANDROID_HOME.

    You should update your environment configuration to either
    not set ANDROID_SDK_ROOT, or set both environment variables
    to the samepath.
"""


@pytest.mark.parametrize(
    ("message", "title", "width", "expected"),
    [
        # Default width (80) with title and message
        (
            test_message,
            test_title,
            80,
            """\
********************************************************************************
**        WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are inconsistent         **
********************************************************************************
The ANDROID_HOME and ANDROID_SDK_ROOT environment variables are set to different
paths:

    ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
    ANDROID_SDK_ROOT:
    /home/anton/briefcase/tests/console/Console/test_warning_banner.py

 Briefcase will ignore ANDROID_SDK_ROOT and only use the path specified by
 ANDROID_HOME.

You should update your environment configuration to either not set
ANDROID_SDK_ROOT, or set both environment variables to the samepath.
********************************************************************************
""",
        ),
        # Narrow width (40) with title and message
        (
            test_message,
            test_title,
            40,
            """\
****************************************
**     WARNING: ANDROID_HOME and      **
** ANDROID_SDK_ROOT are inconsistent  **
****************************************
The ANDROID_HOME and ANDROID_SDK_ROOT
environment variables are set to
different paths:

    ANDROID_HOME:     /briefcase/tests/c
    onsole/Console/test_warning_banner.p
    y
    ANDROID_SDK_ROOT: /home/anton/briefc
    ase/tests/console/Console/test_warni
    ng_banner.py

 Briefcase will ignore ANDROID_SDK_ROOT
 and only use the path specified by
 ANDROID_HOME.

You should update your environment
configuration to either not set
ANDROID_SDK_ROOT, or set both
environment variables to the samepath.
****************************************
""",
        ),
        # Default width (80) without title
        (
            test_message,
            None,
            80,
            """\
********************************************************************************
The ANDROID_HOME and ANDROID_SDK_ROOT environment variables are set to different
paths:

    ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
    ANDROID_SDK_ROOT:
    /home/anton/briefcase/tests/console/Console/test_warning_banner.py

 Briefcase will ignore ANDROID_SDK_ROOT and only use the path specified by
 ANDROID_HOME.

You should update your environment configuration to either not set
ANDROID_SDK_ROOT, or set both environment variables to the samepath.
********************************************************************************
""",
        ),
        # Custom width (60) with title and message
        (
            test_message,
            test_title,
            60,
            """\
************************************************************
**     WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are     **
**                      inconsistent                      **
************************************************************
The ANDROID_HOME and ANDROID_SDK_ROOT environment variables
are set to different paths:

    ANDROID_HOME:
    /briefcase/tests/console/Console/test_warning_banner.py
    ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Co
    nsole/test_warning_banner.py

 Briefcase will ignore ANDROID_SDK_ROOT and only use the
 path specified by ANDROID_HOME.

You should update your environment configuration to either
not set ANDROID_SDK_ROOT, or set both environment variables
to the samepath.
************************************************************
""",
        ),
        # Very narrow width (30) with title and message
        (
            test_message,
            test_title,
            31,
            # codespell: ignore
            """\
*******************************
** WARNING: ANDROID_HOME and **
**    ANDROID_SDK_ROOT are   **
**        inconsistent       **
*******************************
The ANDROID_HOME and
ANDROID_SDK_ROOT environment
variables are set to different
paths:

    ANDROID_HOME:     /briefcas
    e/tests/console/Console/tes
    t_warning_banner.py
    ANDROID_SDK_ROOT: /home/ant
    on/briefcase/tests/console/
    Console/test_warning_banner
    .py

 Briefcase will ignore
 ANDROID_SDK_ROOT and only use
 the path specified by
 ANDROID_HOME.

You should update your
environment configuration to
either not set
ANDROID_SDK_ROOT, or set both
environment variables to the
samepath.
*******************************
""",
        ),
        # Message with only title (empty message)
        (
            "",
            test_title,
            80,
            """\
********************************************************************************
**        WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are inconsistent         **
********************************************************************************
""",
        ),
        # Very short message with title
        (
            "Short message",
            "Short title",
            80,
            """\
********************************************************************************
**                            WARNING: Short title                            **
********************************************************************************
Short message
********************************************************************************
""",
        ),
        # Message and title lengths equal to box width
        (
            "Length of message is equal to box _width",
            "Length of ......... width",
            40,
            """\
****************************************
** WARNING: Length of ......... width **
****************************************
Length of message is equal to box _width
****************************************
""",
        ),
        # Message and title lengths longer +1 symbol to box width
        (
            "Length of message +is equal to box _width",
            "Length of ......+... width",
            40,
            """\
****************************************
**   WARNING: Length of ......+...    **
**               width                **
****************************************
Length of message +is equal to box
_width
****************************************
""",
        ),
    ],
)
def test_warning_banner(console, message, title, width, expected, capsys):
    """Test warning_banner with various inputs."""

    # call the function
    console.warning_banner(message=message, title=title, width=width)
    # capture console output
    output = capsys.readouterr().out

    assert expected == output


@pytest.mark.parametrize(
    ("message", "title", "width", "expected_error"),
    [
        ("", "", 80, "Message or title must be provided"),
        ("message", "title", "80", "Width must be an integer"),
        (777, "title", 80, "Message must be a string"),
        ("message", 777, 80, "Title must be a string"),
    ],
)
def test_warning_banner_with_invalid_inputs(
    console, message, title, width, expected_error
):
    """Test warning_banner with various invalid inputs."""

    with pytest.raises((ValueError, TypeError), match=expected_error):
        console.warning_banner(message=message, title=title, width=width)
