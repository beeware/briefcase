from briefcase.console import Console


def test_default_constructor():
    """A console is enabled by default."""
    console = Console()
    assert console.input_enabled


def test_constructor_with_enabled_false():
    """A console can be constructed in a disabled state."""
    console = Console(input_enabled=False)
    assert not console.input_enabled


def test_enable(disabled_console):
    """A disabled console can be enabled."""
    assert not disabled_console.input_enabled

    disabled_console.input_enabled = True

    assert disabled_console.input_enabled


def test_disable():
    """A disabled console can be enabled."""
    console = Console()
    assert console.input_enabled

    console.input_enabled = False
    assert not console.input_enabled


def test_is_interactive_non_interactive(non_interactive_console):
    """Console is non-interactive when stdout has no tty."""
    assert non_interactive_console.is_interactive is False


def test_is_interactive_always_interactive(console):
    """Console is interactive when stdout has a tty."""
    assert console.is_interactive is True
