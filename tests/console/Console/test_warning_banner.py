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
        # Test 1: Empty message and title
        ("", "", 80, ""),
        # Test 2: Default width (80) with title and message
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
        # Test 3: Narrow width (40) with title and message
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
        # Test 4: Default width (80) without title
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
        # Test 5: Custom width (60) with title and message
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
        # Test 6: Very narrow width (30) with title and message
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
        # Test 7: Message with only title (empty message)
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
        # Test 8: Very short message with title
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
        # Test 9: Message and title lengths equal to box width
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
        # Test 10: Message and title lengths longer +1 symbol to box width
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
        # Test 11: Invalid input type of message
        (
            777,
            "title",
            40,
            "",
        ),
        # Test 12: Invalid input type of title
        (
            "message",
            777,
            40,
            "",
        ),
        # Test 13: Invalid input type of width
        (
            "message",
            "title",
            "40",
            "",
        ),
    ],
    ids=[
        "test-1",
        "test-2",
        "test-3",
        "test-4",
        "test-5",
        "test-6",
        "test-7",
        "test-8",
        "test-9",
        "test-10",
        "test-11",
        "test-12",
        "test-13",
    ],
)
def test_warning_banner(console, message, title, width, expected):
    """Test warning_banner with various inputs."""

    msg = console.warning_banner(message, title=title, width=width)

    assert msg == expected
