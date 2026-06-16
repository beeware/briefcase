import pytest


@pytest.mark.parametrize("args", [[], ["python", "-m", "pip", "install", "package"]])
def test_rewrite_args(noop_venv, args):
    """`rewrite_args` returns the args unmodified."""
    assert args is noop_venv.rewrite_args(args)
