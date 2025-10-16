from textwrap import dedent

import pytest

from briefcase.platforms.windows import txt_to_rtf


@pytest.mark.parametrize(
    "input, expected",
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
    ],
)
def test_txt_to_rtf(input, expected):
    """Utility method can convert TXT to RTF format."""
    assert txt_to_rtf(dedent(input)) == dedent(expected)
