import pytest

from briefcase.integrations.subprocess import ParseError, json_parser


@pytest.mark.parametrize(
    "data, output",
    [
        ('{"key": "value"}', {"key": "value"}),
        (b'{"key": "value"}', {"key": "value"}),
    ],
)
def test_json_parser_success(data, output):
    assert json_parser(data) == output


@pytest.mark.parametrize(
    "data",
    (
        'This is a prologue in my JSON output :( \n\n{"key": "value"}',
        b'This is a prologue in my JSON output :( \n\n{"key": "value"}',
    ),
)
def test_json_parser_fail(data):
    with pytest.raises(ParseError, match="Failed to parse output as JSON:"):
        json_parser(data)
