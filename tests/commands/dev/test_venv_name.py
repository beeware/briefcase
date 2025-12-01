import importlib.machinery


def test_venv_name(monkeypatch, dev_command):
    """Name of the venv is platform specific."""
    # Set up some fake platform details
    monkeypatch.setattr(
        importlib.machinery,
        "EXTENSION_SUFFIXES",
        [".cpython-3X-gothic.so", ".cpython-abi3.so", ".so"],
    )

    assert dev_command.venv_name == "dev.cpython-3X-gothic"
