import sys
from unittest.mock import call

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(dev_command, first_app):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    dev_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        dev_command()

    # No apps will be launched
    assert dev_command.subprocess.run.call_args_list == []


def test_no_args_one_app(dev_command, first_app, environment):
    "If there is one app, dev starts that app by default"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'first'], check=True, env=environment)
    ]


def test_no_args_two_apps(dev_command, first_app, second_app):
    "If there are one app, dev starts that app by default"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # No apps will be launched
    assert dev_command.subprocess.run.call_args_list == []


def test_with_arg_one_app(dev_command, first_app, environment):
    "If there is one app, and a -a argument, dev starts that app"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure a -a command line option
    options = dev_command.parse_options(['-a', 'first'])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'first'], check=True, env=environment)
    ]


def test_with_arg_two_apps(dev_command, first_app, second_app, environment):
    "If there are multiple apps, the --app argument starts app nominated"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = dev_command.parse_options(['--app', 'second'])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'second'], check=True, env=environment)
    ]


def test_bad_app_reference(dev_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = dev_command.parse_options(['--app', 'does-not-exist'])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # No apps will be launched
    assert dev_command.subprocess.run.call_args_list == []


def test_update_dependencies(dev_command, first_app, environment):
    "The dev command can request that the app is updated first"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options(['-d'])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'first'], check=True, env=environment)
    ]


def test_run_uninstalled(dev_command, first_app_uninstalled, environment):
    "The dev command will install first if the app hasn't been installed"
    # Add a single app
    dev_command.apps = {
        'first': first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'first'], check=True, env=environment)
    ]


def test_update_uninstalled(dev_command, first_app_uninstalled, environment):
    "A request to update dependencies is redundant if the app hasn't been installed"
    # Add a single app
    dev_command.apps = {
        'first': first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options(['-d'])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'first'], check=True, env=environment)
    ]


@pytest.mark.skipif(sys.platform != "windows", reason="separator does not fit with windows syntax")
def test_no_args_one_app_with_two_sources_on_non_windows(dev_command, third_app, environment):
    "when running test with 2 sources on linux or mac, it adds them in PYTHONPATH with : separtor"

    # Add a single app
    dev_command.apps = {
        'third': third_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src:src2"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'third'], check=True, env=environment)
    ]


@pytest.mark.skipif(sys.platform == "windows", reason="separator only fits with windows syntax")
def test_no_args_one_app_with_two_sources_on_windows(dev_command, third_app, environment):
    "when running test with 2 sources on linux or mac, it adds them in PYTHONPATH with ; separtor"
    # Add a single app
    dev_command.apps = {
        'third': third_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    environment["PYTHONPATH"] = "src;src2"
    assert dev_command.subprocess.run.call_args_list == [
        call([sys.executable, '-m', 'third'], check=True, env=environment)
    ]
