from briefcase.utils import format_message_to_asterisk_box

name = "Anton"
issue_idx = 2559

source_msg = (
    f"Hi there! My name is {name}, and I'm a Python developer.\n\n"
    "This is my very first experience in open source development. "
    "I like your project, and I'm excited to contribute to it."
)
source_title = (
    f"INFO: I TRIED TO SOLVE THIS ISSUE #{issue_idx}. "
    "IT SEEMED TO ME RATHER SIMPLE, "
    "BUT I GOT VERY GOOD EXPERIENCE"
)


def test_format_message_to_asterisk_box_empty_string_title():
    # Test with empty message and title
    msg = format_message_to_asterisk_box("")

    assert msg == ""


def test_format_message_to_asterisk_box_width_80_default():
    # Test with width 80: default
    msg = format_message_to_asterisk_box(
        source_msg,
        title=source_title,
    )
    output_msg_width_80_default = (
        "*" * 79
        + """*
**  INFO: I TRIED TO SOLVE THIS ISSUE #2559. IT SEEMED TO ME RATHER SIMPLE,   **
**                       BUT I GOT VERY GOOD EXPERIENCE                       **
********************************************************************************
Hi there! My name is Anton, and I'm a Python developer.

This is my very first experience in open source development. I like your
project, and I'm excited to contribute to it.
********************************************************************************"""
    )
    assert msg == output_msg_width_80_default


def test_format_message_to_asterisk_box_width_40_default():
    # Test with width 40: very narrow
    msg = format_message_to_asterisk_box(
        source_msg,
        title=source_title,
        width=40,
    )
    output_msg_width_40 = """****************************************
**    INFO: I TRIED TO SOLVE THIS     **
**    ISSUE #2559. IT SEEMED TO ME    **
**   RATHER SIMPLE, BUT I GOT VERY    **
**          GOOD EXPERIENCE           **
****************************************
Hi there! My name is Anton, and I'm a
Python developer.

This is my very first experience in open
source development. I like your project,
and I'm excited to contribute to it.
****************************************"""
    assert msg == output_msg_width_40


def test_format_message_to_asterisk_box_empty_title():
    # Test with width 80: default
    msg = format_message_to_asterisk_box(
        source_msg,
    )
    output_msg_width_80_default = (
        "*" * 79
        + """*
Hi there! My name is Anton, and I'm a Python developer.

This is my very first experience in open source development. I like your
project, and I'm excited to contribute to it.
********************************************************************************"""
    )
    assert msg == output_msg_width_80_default
