import textwrap


def format_message_to_asterisk_box(
    message: str,
    title: str = "",
    width=80,
    border_char="*",
    padding=2,
) -> str:
    """Format a message to an asterisk box.

    Args:
        message (str): The message to format.
        title (str, optional): The title of the box. Defaults to None.
        width (int, optional): The width of the box. Defaults to 80.
        border_char (str, optional): The character to use for the border.
            Defaults to "*".
        padding (int, optional): The number of spaces to pad the border.
            Defaults to 2.

    Returns:
        str: The formatted message.
    """

    if not message:
        return ""

    # Create border line
    border_line = border_char * width
    # create lines array with opening line of the box
    lines = [border_line]

    # if title exists, format title in the box
    if title:
        # Wrap the title to lines to fit the width of the box
        wrapped_title_lines = textwrap.wrap(
            title.strip(),
            width=width - (padding * 2) - 4,
        )

        # width of title line inside the box
        inner_width = width - (padding * 2)

        for line in wrapped_title_lines:
            # Center each line within the available space
            padded_line = line.center(inner_width)
            # add line to the box
            lines.append(f"**{padded_line}**")

        # closing line of title in the box
        lines.append(border_line)

    # split the message into paragraphs
    paragraphs = message.split("\n")
    for paragraph in paragraphs:
        if paragraph.strip():  # Non-empty paragraph
            # Wrap paragraph to lines to fit the width of the box
            wrapped_lines = textwrap.wrap(paragraph, width=width)
            lines.extend(wrapped_lines)
        else:  # Empty paragraph (preserve blank lines)
            lines.append("")

    # closing line of message
    lines.append(border_line)

    # merge lines into a single string and return
    return "\n".join(lines)
