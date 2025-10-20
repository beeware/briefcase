import pytest


def test_command_contract(cfg_mod):
    cmd = cfg_mod.ConfigCommand(
        console=type(
            "C",
            (),
            {
                "print": lambda *a, **k: None,
                "info": lambda *a, **k: None,
                "warning": lambda *a, **k: None,
                "error": lambda *a, **k: None,
            },
        )()
    )
    assert cmd.command == "config"
    assert cmd.platform is None  # you set this already
    assert isinstance(cmd.description, str) and cmd.description


def test_placeholders_raise(cfg_mod):
    cmd = cfg_mod.ConfigCommand(
        console=type(
            "C",
            (),
            {
                "print": lambda *a, **k: None,
                "info": lambda *a, **k: None,
                "warning": lambda *a, **k: None,
                "error": lambda *a, **k: None,
            },
        )()
    )
    # Keep only the placeholders that actually exist & raise in your class

    with pytest.raises(NotImplementedError):
        cmd.bundle_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_path(None)
    with pytest.raises(NotImplementedError):
        cmd.distribution_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_executable_path(None)
