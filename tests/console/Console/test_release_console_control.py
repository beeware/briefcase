from unittest.mock import Mock


def test_console_is_controlled(console):
    """Console control is released and then restored."""

    console.is_console_controlled = True

    with console.release_console_control():
        assert console.is_console_controlled is False

    assert console.is_console_controlled is True


def test_console_is_not_controlled(console):
    """Effective no-op when console is not currently controlled."""
    assert console.is_console_controlled is False

    with console.release_console_control():
        assert console.is_console_controlled is False

    assert console.is_console_controlled is False


def test_wait_bar_is_active(console):
    """An active Wait Bar is stopped."""
    with console.wait_bar("Testing..."):
        # Wrap the Wait Bar stop and start methods
        console._wait_bar.stop = Mock(wraps=console._wait_bar.stop)
        console._wait_bar.start = Mock(wraps=console._wait_bar.start)

        # Wait Bar is active
        assert console._wait_bar.live.is_started is True
        assert console.is_console_controlled is True

        with console.release_console_control():
            # Wait Bar is not active
            console._wait_bar.stop.assert_called_once()
            assert console._wait_bar.live.is_started is False
            assert console.is_console_controlled is False

        # Wait bar is restored and active again
        console._wait_bar.stop.assert_called_once()
        assert console._wait_bar.live.is_started is True
        assert console.is_console_controlled is True


def test_wait_bar_is_not_active(console):
    """An inactive Wait Bar is not effected."""
    # Instantiate the Wait Bar
    with console.wait_bar("Testing..."):
        pass

    # Mock the Wait Bar stop and start methods
    console._wait_bar.stop = Mock(wraps=console._wait_bar.stop)
    console._wait_bar.start = Mock(wraps=console._wait_bar.start)

    assert console._wait_bar.live.is_started is False
    assert console.is_console_controlled is False

    with console.release_console_control():
        # A stop request was not made for the Wait Bar
        console._wait_bar.stop.assert_not_called()
        assert console._wait_bar.live.is_started is False
        assert console.is_console_controlled is False

    # A start request was not made for the Wait Bar
    console._wait_bar.start.assert_not_called()
    assert console._wait_bar.live.is_started is False
    assert console.is_console_controlled is False
