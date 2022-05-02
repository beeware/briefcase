import pytest

from briefcase.integrations.subprocess import ParserError, json_parser


@pytest.mark.parametrize("data", ('{"key": "value"}', b'{"key": "value"}'))
def test_json_parser_success(data):
    parsed_json = json_parser(data)
    assert parsed_json == {"key": "value"}


@pytest.mark.parametrize(
    "data",
    (
            'This is a prologue in my JSON output :( \n\n{"key": "value"}',
            b'This is a prologue in my JSON output :( \n\n{"key": "value"}'
    )
)
def test_json_parser_fail(data):
    with pytest.raises(ParserError, match="Failed to parse output as JSON:"):
        json_parser(data)
