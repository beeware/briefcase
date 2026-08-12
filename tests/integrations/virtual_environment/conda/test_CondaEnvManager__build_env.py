import pytest


@pytest.mark.parametrize("env", [None, {}, {"CUSTOM": "value", "PATH": "/x"}])
def test_build_env(venv, env):
    """The environment isn't modified."""
    assert venv.build_env(env) is env
