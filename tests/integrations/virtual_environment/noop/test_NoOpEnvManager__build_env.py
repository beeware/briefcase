import pytest


@pytest.mark.parametrize("env", [None, {}, {"CUSTOM": "value", "PATH": "/x"}])
def test_build_env(noop_venv, env):
    """The environment isn't modified."""
    assert noop_venv.build_env(env) is env
