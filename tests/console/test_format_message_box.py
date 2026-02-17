from briefcase.console import MAX_TEXT_WIDTH, format_message_box


def test_format_message_box_title_alignment():
    """A title line is always aligned with the message border."""
    title = "WARNING: JAVA_HOME does not point to a Java 17 JDK"

    lines = format_message_box("Briefcase will proceed.", title=title).splitlines()

    assert lines[0] == "*" * MAX_TEXT_WIDTH
    assert lines[1] == f"** {title:<{MAX_TEXT_WIDTH - 6}} **"
    assert lines[2] == "*" * MAX_TEXT_WIDTH
    assert lines[-1] == "*" * MAX_TEXT_WIDTH


def test_format_message_box_wraps_content():
    """Body content is wrapped and indented to fit inside the message box."""
    message = (
        "This is a deliberately long line that should be wrapped by the helper to "
        "fit cleanly inside the message box body."
    )

    lines = format_message_box(message).splitlines()

    assert lines[0] == "*" * MAX_TEXT_WIDTH
    assert lines[-1] == "*" * MAX_TEXT_WIDTH

    for line in lines[2:-1]:
        if line:
            assert line.startswith("    ")
        assert len(line) <= MAX_TEXT_WIDTH
