import sys
from subprocess import CalledProcessError
import pytest

from briefcase.exceptions import BriefcaseCommandError


def raise_called_process_error(*args, **kwargs):
    raise CalledProcessError(returncode=2, cmd="cmd")


def test_subprocess_running_successfully(dev_command, first_app):
    env = dict(a=1, b=2, c=3)
    dev_command.run_dev_app(first_app, env)
    dev_command.subprocess.run.assert_called_once_with([sys.executable, '-m', first_app.app_name],
                                                       env=env,
                                                       check=True)


def test_subprocess_throws_error(dev_command, first_app):
    env = dict(a=1, b=2, c=3)
    dev_command.subprocess.run.side_effect = raise_called_process_error
    with pytest.raises(BriefcaseCommandError, match="Unable to start application 'first'"):
        dev_command.run_dev_app(first_app, env)
    dev_command.subprocess.run.assert_called_once_with([sys.executable, '-m', first_app.app_name],
                                                       env=env,
                                                       check=True)
