from briefcase.commands.config import get_config, set_config


def test_set_config_creates_nested_tables_and_sets_value():
    data = {}

    # Single-segment (no loop), just sanity
    set_config(data, "author", {})
    assert get_config(data, "author") == {}

    # Dotted key (enters the for-loop starting at 146)
    set_config(data, "author.name", "Jane")
    assert get_config(data, "author.name") == "Jane"

    set_config(data, "android.device", "@Pixel_5")
    assert get_config(data, "android.device") == "@Pixel_5"
