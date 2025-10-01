from pathlib import Path

import pytest
import tomli_w


def _parse(parser, argv):
    return vars(parser.parse_args(argv))


def test_no_operation_errors(make_cmd_and_parser, force_global_path, cfg_mod):
    cmd, parser, console = make_cmd_and_parser()
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(**_parse(parser, ["--global"]))


def test_multiple_operations_errors(make_cmd_and_parser, force_global_path, capsys):
    cmd, parser, console = make_cmd_and_parser()

    # Mutually exclusive options conflict is a *parse-time* error.
    with pytest.raises(SystemExit) as e:
        parser.parse_args(["--global", "--get", "author.name", "--list"])

    # argparse uses exit code 2 for usage errors
    assert e.value.code == 2

    # Helpful message is printed to stderr by argparse
    err = capsys.readouterr().err
    assert "not allowed with argument --get" in err


@pytest.mark.parametrize("key", ["android.device", "iOS.device"])
def test_question_sentinel_allowed_for_devices(
    make_cmd_and_parser, force_global_path, key
):
    cmd, parser, console = make_cmd_and_parser()
    cmd.__call__(**_parse(parser, ["--global", key, "?"]))
    text = force_global_path.read_text(encoding="utf-8")
    assert "?" in text and key.split(".")[0] in text


def test_question_sentinel_rejected_elsewhere(
    make_cmd_and_parser, force_global_path, cfg_mod
):
    cmd, parser, console = make_cmd_and_parser()
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(**_parse(parser, ["--global", "author.email", "?"]))


def test_list_empty_file_prints_empty_marker(
    make_cmd_and_parser, tmp_path, monkeypatch, cfg_mod
):
    # Point to a fresh path so file is missing/empty
    fresh = tmp_path / "fresh" / "config.toml"
    monkeypatch.setattr(
        cfg_mod,
        "scope_path",
        lambda pr, is_global: fresh
        if is_global
        else Path(pr) / ".briefcase" / "config.toml",
        raising=True,
    )
    cmd, parser, console = make_cmd_and_parser()
    cmd.__call__(**_parse(parser, ["--global", "--list"]))
    out = console.getvalue()
    assert "(empty)" in out and str(fresh) in out


def test_get_missing_key_is_graceful(make_cmd_and_parser, force_global_path):
    # Prewrite some other content
    force_global_path.parent.mkdir(parents=True, exist_ok=True)
    force_global_path.write_text(
        tomli_w.dumps({"author": {"name": "Jane"}}), encoding="utf-8"
    )

    cmd, parser, console = make_cmd_and_parser()
    cmd.__call__(**_parse(parser, ["--global", "--get", "author.email"]))
    out = console.getvalue()
    assert "Jane" not in out  # don’t leak wrong value


def test_unset_missing_key_is_graceful(make_cmd_and_parser, force_global_path):
    # Start with empty file
    force_global_path.parent.mkdir(parents=True, exist_ok=True)
    force_global_path.write_text(tomli_w.dumps({}), encoding="utf-8")
    cmd, parser, console = make_cmd_and_parser()
    cmd.__call__(**_parse(parser, ["--global", "--unset", "author.email"]))
    out = console.getvalue()
    # Implementation usually prints a 'not present' kind of line containing the key:
    assert "author.email" in out


def test_read_toml_invalid_raises(make_cmd_and_parser, force_global_path, cfg_mod):
    # Write definitely invalid TOML
    force_global_path.parent.mkdir(parents=True, exist_ok=True)
    force_global_path.write_text(
        "author = { email = 'missing_quote }", encoding="utf-8"
    )
    cmd, parser, console = make_cmd_and_parser()
    import pytest

    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(**_parse(parser, ["--global", "--list"]))


def test_write_error_surfaces_as_briefcase_error(
    make_cmd_and_parser, monkeypatch, cfg_mod
):
    # Patch Path.open so that opening for write raises OSError.
    orig_open = Path.open

    def boom_open(self, mode="r", *args, **kwargs):
        # write branch used by write_toml -> trigger failure
        if "w" in mode:
            raise OSError("disk full")
        # allow non-write modes to work normally if they ever occur
        return orig_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", boom_open, raising=True)

    cmd, parser, console = make_cmd_and_parser()

    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(**vars(parser.parse_args(["--global", "author.name", "X"])))


def test_unknown_key_rejected(make_cmd_and_parser, force_global_path, cfg_mod):
    cmd, parser, console = make_cmd_and_parser()
    import pytest

    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(**_parse(parser, ["--global", "foo.bar", "baz"]))


def test_invalid_value_rejected(make_cmd_and_parser, force_global_path, cfg_mod):
    cmd, parser, console = make_cmd_and_parser()
    import pytest

    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cmd.__call__(
            **_parse(parser, ["--global", "android.device", "R58N42ABCD"])
        )  # invalid pattern
