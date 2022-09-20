from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import RGBExtension


@pytest.mark.parametrize(
    "value, red, green, blue",
    [
        ("#000000", 0.0, 0.0, 0.0),
        ("#FFFFFF", 1.0, 1.0, 1.0),
        ("#336699", 0.2, 0.4, 0.6),
        ("#abcdef", 0.6705882, 0.8039215, 0.9372549),
        # Not a color RGB hexstring
        ("hoovaloo", 1.0, 1.0, 1.0),
    ],
)
def test_py_tag(value, red, green, blue):
    env = MagicMock()
    env.filters = {}
    RGBExtension(env)
    assert env.filters["float_red"](value) == pytest.approx(red)
    assert env.filters["float_green"](value) == pytest.approx(green)
    assert env.filters["float_blue"](value) == pytest.approx(blue)
