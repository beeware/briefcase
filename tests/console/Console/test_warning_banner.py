import pytest

source_msg = """\
            Hi there! My name is Anton, and I'm a Python developer.\\n\\n
            This is my very first
            experience in open source
            development.
            I like your project, and I'm excited to contribute to it.\
"""

source_title = """\
                INFO: I TRIED TO SOLVE THIS ISSUE #2559.\\n\\n
                IT SEEMED TO ME RATHER SIMPLE,
                BUT I GOT VERY GOOD EXPERIENCE\
"""


@pytest.mark.parametrize(
    ("message", "title", "width", "expected"),
    [
        # Default width (80) with title and message
        (
            source_msg,
            source_title,
            80,
            """\
********************************************************************************
**                  INFO: I TRIED TO SOLVE THIS ISSUE #2559.                  **
**                                                                            **
**       IT SEEMED TO ME RATHER SIMPLE, BUT I GOT VERY GOOD EXPERIENCE        **
********************************************************************************
Hi there! My name is Anton, and I'm a Python developer.

This is my very first experience in open source development. I like your
project, and I'm excited to contribute to it.
********************************************************************************\
""",
        ),
        # Narrow width (40) with title and message
        (
            source_msg,
            source_title,
            40,
            """\
****************************************
** INFO: I TRIED TO SOLVE THIS ISSUE  **
**               #2559.               **
**                                    **
** IT SEEMED TO ME RATHER SIMPLE, BUT **
**     I GOT VERY GOOD EXPERIENCE     **
****************************************
Hi there! My name is Anton, and I'm a
Python developer.

This is my very first experience in open
source development. I like your project,
and I'm excited to contribute to it.
****************************************\
""",
        ),
        # Default width (80) without title
        (
            source_msg,
            None,
            80,
            """\
********************************************************************************
Hi there! My name is Anton, and I'm a Python developer.

This is my very first experience in open source development. I like your
project, and I'm excited to contribute to it.
********************************************************************************\
""",
        ),
        # Custom width (60) with title and message
        (
            source_msg,
            source_title,
            60,
            """\
************************************************************
**        INFO: I TRIED TO SOLVE THIS ISSUE #2559.        **
**                                                        **
**   IT SEEMED TO ME RATHER SIMPLE, BUT I GOT VERY GOOD   **
**                       EXPERIENCE                       **
************************************************************
Hi there! My name is Anton, and I'm a Python developer.

This is my very first experience in open source development.
I like your project, and I'm excited to contribute to it.
************************************************************\
""",
        ),
        # Very narrow width (30) with title and message
        (
            source_msg,
            source_title,
            30,
            """\
******************************
**  INFO: I TRIED TO SOLVE  **
**    THIS ISSUE #2559.     **
**                          **
**  IT SEEMED TO ME RATHER  **
**  SIMPLE, BUT I GOT VERY  **
**     GOOD EXPERIENCE      **
******************************
Hi there! My name is Anton,
and I'm a Python developer.

This is my very first
experience in open source
development. I like your
project, and I'm excited to
contribute to it.
******************************\
""",
        ),
        # Message with only title (empty message)
        (
            "",
            source_title,
            80,
            """\
********************************************************************************
**                  INFO: I TRIED TO SOLVE THIS ISSUE #2559.                  **
**                                                                            **
**       IT SEEMED TO ME RATHER SIMPLE, BUT I GOT VERY GOOD EXPERIENCE        **
********************************************************************************\
""",
        ),
        # Very short message with title
        (
            "Short message",
            "Short title",
            80,
            """\
********************************************************************************
**                                Short title                                 **
********************************************************************************
Short message
********************************************************************************\
""",
        ),
        # Message and title lengths equal to box width
        (
            "Length of message is equal to box _width",
            "Length of title is e-l to box w-th",
            40,
            """\
****************************************
** Length of title is e-l to box w-th **
****************************************
Length of message is equal to box _width
****************************************\
""",
        ),
        # Message and title lengths longer +1 symbol to box width
        (
            "Length of message is equal to box __width",
            "Length of title is e-l to box _w-th",
            40,
            """\
****************************************
** Length of title is e-l to box _w-  **
**                 th                 **
****************************************
Length of message is equal to box
__width
****************************************\
""",
        ),
    ],
)
def test_warning_banner(console, message, title, width, expected):
    """Test warning_banner with various inputs."""

    msg = console.warning_banner(message, title=title, width=width)

    assert msg == expected


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
        console.warning_banner(message, title=title, width=width)
