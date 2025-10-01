def _parse(parser, argv):
    return vars(parser.parse_args(argv))


def test_project_set_get_list_unset(monkeypatch, make_cmd_and_parser, make_project):
    proj = make_project
    monkeypatch.chdir(proj)

    cmd, parser, console = make_cmd_and_parser()

    # SET (no --global)
    opts = _parse(parser, ["author.email", "x@ex.com"])
    cmd.__call__(**opts)

    path = proj / ".briefcase" / "config.toml"
    assert path.exists()
    assert 'email = "x@ex.com"' in path.read_text(encoding="utf-8")

    # GET
    console.clear()
    opts = _parse(parser, ["--get", "author.email"])
    cmd.__call__(**opts)
    assert "x@ex.com" in console.getvalue()

    # LIST
    console.clear()
    opts = _parse(parser, ["--list"])
    cmd.__call__(**opts)
    out = console.getvalue()
    assert "[author]" in out and "# file:" in out
