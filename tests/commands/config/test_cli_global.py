def _parse(parser, argv):
    ns = parser.parse_args(argv)
    return vars(ns)


def test_global_set_get_list_unset(make_cmd_and_parser, force_global_path):
    cmd, parser, console = make_cmd_and_parser()

    # SET
    opts = _parse(parser, ["--global", "author.name", "Jane Smith"])
    cmd.__call__(**opts)
    text = force_global_path.read_text(encoding="utf-8")
    assert 'name = "Jane Smith"' in text

    # GET
    console.clear()
    opts = _parse(parser, ["--global", "--get", "author.name"])
    cmd.__call__(**opts)
    assert "Jane Smith" in console.getvalue()

    # LIST (non-empty -> prints TOML + '# file: ...')
    console.clear()
    opts = _parse(parser, ["--global", "--list"])
    cmd.__call__(**opts)
    out = console.getvalue()
    assert "# file:" in out
    assert "[author]" in out

    # UNSET -> then LIST again
    console.clear()
    opts = _parse(parser, ["--global", "--unset", "author.name"])
    cmd.__call__(**opts)

    console.clear()
    opts = _parse(parser, ["--global", "--list"])
    cmd.__call__(**opts)
    out = console.getvalue()
    # After unsetting, your code does NOT prune empty parent tables;
    # so we don't insist on "(empty)"; just ensure the value is gone and a footer exists.
    assert "Jane Smith" not in out
    assert ("# file:" in out) or ("(empty)" in out)
