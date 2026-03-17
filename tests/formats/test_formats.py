from unittest.mock import MagicMock, patch

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats import (
    get_default_packaging_format,
    get_packaging_format,
    get_packaging_formats,
)


@pytest.fixture
def mock_command():
    return MagicMock()


@pytest.fixture
def mock_app():
    return MagicMock()


def test_get_packaging_formats():
    """Built-in and third-party formats can be discovered."""
    with patch("briefcase.formats.entry_points") as mock_entry_points:
        mock_ep1 = MagicMock()
        mock_ep1.name = "format1"
        mock_ep1.load.return_value = "Class1"

        mock_ep2 = MagicMock()
        mock_ep2.name = "format2"
        mock_ep2.load.return_value = "Class2"

        mock_entry_points.return_value = [mock_ep1, mock_ep2]

        formats = get_packaging_formats("macOS", "app")
        assert formats == {"format1": "Class1", "format2": "Class2"}
        mock_entry_points.assert_called_once_with(group="briefcase.formats.macOS.app")


def test_get_packaging_format_success(mock_command):
    """An instantiated packaging format can be retrieved by name."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        mock_class = MagicMock()
        mock_get_formats.return_value = {"test": mock_class}

        fmt = get_packaging_format("test", "macOS", "app", mock_command)

        assert fmt == mock_class.return_value
        mock_class.assert_called_once_with(command=mock_command)


def test_get_packaging_format_unknown(mock_command):
    """If a format is unknown, an error is raised."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        mock_get_formats.return_value = {"other": MagicMock()}

        with pytest.raises(
            BriefcaseCommandError, match="Unknown packaging format: test"
        ):
            get_packaging_format("test", "macOS", "app", mock_command)


def test_get_default_packaging_format_success(mock_command, mock_app):
    """The default format is the one with the highest priority."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        # Define some mock format classes
        format1_class = MagicMock()
        format1_class.return_value.priority.return_value = 5

        format2_class = MagicMock()
        format2_class.return_value.priority.return_value = 10

        format3_class = MagicMock()
        format3_class.return_value.priority.return_value = 0  # Not usable

        mock_get_formats.return_value = {
            "low": format1_class,
            "high": format2_class,
            "unusable": format3_class,
        }

        default = get_default_packaging_format("macOS", "app", mock_app, mock_command)

        assert default == "high"


def test_get_default_packaging_format_tie(mock_command, mock_app):
    """If there's a tie in priority, the first in sorted order wins."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        format1_class = MagicMock()
        format1_class.return_value.priority.return_value = 10

        format2_class = MagicMock()
        format2_class.return_value.priority.return_value = 10

        mock_get_formats.return_value = {
            "beta": format2_class,
            "alpha": format1_class,
        }

        default = get_default_packaging_format("macOS", "app", mock_app, mock_command)

        assert default == "alpha"


def test_get_default_packaging_format_none_available(mock_command, mock_app):
    """If no formats are available (priority 0 or none discovered), an error is
    raised."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        format_class = MagicMock()
        format_class.return_value.priority.return_value = 0

        mock_get_formats.return_value = {"unusable": format_class}

        with pytest.raises(
            BriefcaseCommandError, match="No packaging formats are available"
        ):
            get_default_packaging_format("macOS", "app", mock_app, mock_command)


def test_get_default_packaging_format_priority_error(mock_command, mock_app):
    """If a priority check fails, it's ignored."""
    with patch("briefcase.formats.get_packaging_formats") as mock_get_formats:
        format1_class = MagicMock()
        format1_class.return_value.priority.side_effect = Exception("Boom")

        format2_class = MagicMock()
        format2_class.return_value.priority.return_value = 5

        mock_get_formats.return_value = {
            "broken": format1_class,
            "working": format2_class,
        }

        default = get_default_packaging_format("macOS", "app", mock_app, mock_command)

        assert default == "working"
