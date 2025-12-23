import pytest

name = "Anton"
issue_idx = 2559

source_msg = f"""\
            Hi there! My name is {name}, and I'm a Python developer.\\n\\n
            This is my very first
            experience in open source
            development.
            I like your project, and I'm excited to contribute to it.\
"""

source_title = f"""\
                \\nINFO: I TRIED TO SOLVE THIS ISSUE #{issue_idx}.\\n\\n
                IT SEEMED TO ME RATHER SIMPLE,
                BUT I GOT VERY GOOD EXPERIENCE\
"""


@pytest.mark.parametrize(
    ("test_name", "message", "title", "width", "expected"),
    [
        ("Test 1: Empty message and title", "", "", 80, ""),
        (
            "Test 2: Default width (80) with title and message",
            source_msg,
            source_title,
            80,
            """\
********************************************************************************
**                                                                            **
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
        (
            "Test 3: Narrow width (40) with title and message",
            source_msg,
            source_title,
            40,
            """\
****************************************
**                                    **
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
        (
            "Test 4: Default width (80) without title",
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
        (
            "Test 5: Custom width (60) with title and message",
            source_msg,
            source_title,
            60,
            """\
************************************************************
**                                                        **
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
        (
            "Test 6: Very narrow width (30) with title and message",
            source_msg,
            source_title,
            30,
            """\
******************************
**                          **
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
        (
            "Test 7: Message with only title (empty message)",
            "",
            source_title,
            80,
            """\
********************************************************************************
**                                                                            **
**                  INFO: I TRIED TO SOLVE THIS ISSUE #2559.                  **
**                                                                            **
**       IT SEEMED TO ME RATHER SIMPLE, BUT I GOT VERY GOOD EXPERIENCE        **
********************************************************************************\
""",
        ),
        (
            "Test 8: Very short message with title",
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
        (
            "Test 9: Message and title lengths equal to box width",
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
        (
            "Test 10: Message and title lengths longer +1 symbol to box width",
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
        # (
        #     "Test 9: Message and title lengths equal to box width",
        #     5,
        #     5,
        #     40,
        #     "",
        # ),
    ],
)
def test_warning_banner(console, test_name, message, title, width, expected):
    """Test warning_banner with various inputs."""
    if title is None:
        msg = console.warning_banner(message, width=width)
    else:
        msg = console.warning_banner(message, title=title, width=width)

    # # Debug output if needed
    # print('\n\n' + test_name)
    # print("Generated:")
    # print(msg)
    # print("Expected:")
    # print(expected)

    assert msg == expected
