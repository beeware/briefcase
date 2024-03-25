from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import PListExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, "<true/>"),
        (False, "<false/>"),
        ("Hello world", "<string>Hello world</string>"),
        (
            ["hello", "world", True],
            "<array>\n"
            "        <string>hello</string>\n"
            "        <string>world</string>\n"
            "        <true/>\n"
            "    </array>",
        ),
        (
            {"hello": "world", "goodbye": False},
            "<dict>\n"
            "        <key>hello</key>\n"
            "        <string>world</string>\n"
            "        <key>goodbye</key>\n"
            "        <false/>\n"
            "    </dict>",
        ),
    ],
)
def test_plist_value(value, expected):
    env = MagicMock()
    env.filters = {}
    PListExtension(env)
    assert env.filters["plist_value"](value) == expected
