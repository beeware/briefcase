def test_wait_bar_always_interactive(interactive_console):
    """Progress Bar is not disabled when console is interactive."""
    with interactive_console.progress_bar() as bar:
        assert bar.disable is False


def test_wait_bar_non_interactive(non_interactive_console):
    """Progress Bar is disabled when console is non-interactive."""
    with non_interactive_console.progress_bar() as bar:
        assert bar.disable is True
