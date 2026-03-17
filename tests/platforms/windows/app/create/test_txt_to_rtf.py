from textwrap import dedent

import pytest

from briefcase.platforms.windows import txt_to_rtf

RTF_HEADER = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}"
RTF_SEPARATOR = "\\par\\line\\brdrb\\brdrs\\brdrw10\\brsp20\\par\\line"


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        pytest.param(
            "",
            "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}\n\\par\\line\n}",
            id="empty-doc",
        ),
        pytest.param(
            """\
            Hello World.

            This is a 2 paragraph document
            with a multi-line paragraph.
            """,
            """\
            {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}
            Hello World.\x20
            \\par\\line
            This is a 2 paragraph document\x20
            with a multi-line paragraph.\x20
            \\par\\line
            }""",
            id="2-para-document",
        ),
        pytest.param(
            """\
            This is a document that contains bullet points:

             * first, something short
             * then, something longer that needs to
               run onto multiple lines
             * last, something short again

            Then a closing paragraph.
            """,
            """\
            {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}
            This is a document that contains bullet points:\x20
            \\par\\line
            \\bullet first, something short\x20
            \\bullet then, something longer that needs to\x20
            run onto multiple lines\x20
            \\bullet last, something short again\x20
            \\par\\line
            Then a closing paragraph.\x20
            \\par\\line
            }""",
            id="bullet-document",
        ),
        pytest.param(
            ["Hello World."],
            """\
            {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}
            Hello World.\x20
            }""",
            id="single-element-list",
        ),
        pytest.param(
            ["Apache License text", "MIT License text"],
            """\
            {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}
            Apache License text\x20
            \\par\\line\\brdrb\\brdrs\\brdrw10\\brsp20\\par\\line
            MIT License text\x20
            }""",
            id="multi-element-list",
        ),
    ],
)
def test_txt_to_rtf(input, expected):
    """Plain text (string or list of strings) is converted to a full RTF document."""
    result = txt_to_rtf(dedent(input) if isinstance(input, str) else input)
    assert result == dedent(expected)
