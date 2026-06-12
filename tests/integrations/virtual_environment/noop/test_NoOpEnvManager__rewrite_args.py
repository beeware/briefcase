import pytest


@pytest.mark.parametrize("args", [[], ["python", "-m", "pip", "install", "package"]])
def test_rewrite_args(venv, args):
    """`rewrite_args` returns the args unmodified."""
    assert args is venv.rewrite_args(args)
