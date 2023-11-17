import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_args_one_app(run_command, first_app):
    """If there is one app, run starts that app by default."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = run_command.parse_options([])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        ("run", "first", {"test_mode": False, "passthrough": []}),
    ]


def test_no_args_one_app_with_passthrough(run_command, first_app):
    """If there is one app, run starts that app by default, and can accept
    passthrough."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = run_command.parse_options(["--", "foo", "--bar"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools have been verified
        ("verify-app-tools", "first"),
        # Run the first app
        ("run", "first", {"test_mode": False, "passthrough": ["foo", "--bar"]}),
    ]


def test_no_args_two_apps(run_command, first_app, second_app):
    """If there are two apps and no explicit app is started, an error is raised."""
    # Add two apps
    run_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = run_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        run_command(**options)

    # No verification actions will be performed
    assert run_command.actions == []


def test_with_arg_one_app(run_command, first_app):
    """If there is one app, and a -a argument, run starts that app."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure a -a command line option
    options, _ = run_command.parse_options(["-a", "first"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        ("run", "first", {"test_mode": False, "passthrough": []}),
    ]


def test_with_arg_two_apps(run_command, first_app, second_app):
    """If there are multiple apps, the --app argument starts app nominated."""
    # Add two apps
    run_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options, _ = run_command.parse_options(["--app", "second"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "second"),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools have been verified
        ("verify-app-tools", "second"),
        # Run the second app
        ("run", "second", {"test_mode": False, "passthrough": []}),
    ]


def test_bad_app_reference(run_command, first_app, second_app):
    """If the command line argument refers to an app that doesn't exist, raise an
    error."""
    # Add two apps
    run_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options, _ = run_command.parse_options(["--app", "does-not-exist"])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        run_command(**options)

    # No verification actions will be performed
    assert run_command.actions == []


def test_create_app_before_start(run_command, first_app_config):
    """If the app to be started doesn't exist, create it first."""
    # Add a single app, using the 'config only' fixture
    run_command.apps = {
        "first": first_app_config,
    }

    # Configure no command line options
    options, _ = run_command.parse_options([])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App doesn't exist, so it will be built
        # (which will transitively create)
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": False,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_build_app_before_start(run_command, first_app_unbuilt):
    """The run command can request that an unbuilt app is compiled first."""
    # Add a single app
    run_command.apps = {
        "first": first_app_unbuilt,
    }

    # Configure no command line options
    options, _ = run_command.parse_options([])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # A build was requested, with no update
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": False,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_update_app(run_command, first_app):
    """The run command can request that the app is updated first."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure an update option
    options, _ = run_command.parse_options(["-u"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # A build with an explicit update was requested
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": True,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_update_app_requirements(run_command, first_app):
    """The run command can request that the app requirements are updated first."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure an update option
    options, _ = run_command.parse_options(["-r"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # A build with an explicit update was requested
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": False,
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_update_app_resources(run_command, first_app):
    """The run command can request that the app resources are updated first."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure an update option
    options, _ = run_command.parse_options(["--update-resources"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # A build with an explicit update was requested
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": False,
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_update_unbuilt_app(run_command, first_app_unbuilt):
    """The run command can request that an unbuilt app is updated first."""
    # Add a single app
    run_command.apps = {
        "first": first_app_unbuilt,
    }

    # Configure an update option
    options, _ = run_command.parse_options(["-u"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # An update was requested, so a build with an explicit update
        # will be performed
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": True,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_update_non_existent(run_command, first_app_config):
    """Requesting an update of a non-existent app causes a create."""
    # Add a single app, using the 'config only' fixture
    run_command.apps = {
        "first": first_app_config,
    }

    # Configure an update option
    options, _ = run_command.parse_options(["-u"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App doesn't exist, so it will be built, with an
        # update requested
        (
            "build",
            "first",
            {
                "test_mode": False,
                "update": True,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": False, "passthrough": []},
        ),
    ]


def test_test_mode_existing_app(run_command, first_app):
    """An existing app can be started in test mode."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["--test"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App is built in test mode
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": False,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": True, "passthrough": []},
        ),
    ]


def test_test_mode_existing_app_with_passthrough(run_command, first_app):
    """An existing app can be started in test mode with passthrough args."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["--test", "--", "foo", "--bar"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App is built in test mode
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": False,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools have been verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {
                "build_state": "first",
                "test_mode": True,
                "passthrough": ["foo", "--bar"],
            },
        ),
    ]


def test_test_mode_existing_app_no_update(run_command, first_app):
    """The auto app update implied by --test can be overridden."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["--test", "--no-update"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App will not be built; update is disabled
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {"test_mode": True, "passthrough": []},
        ),
    ]


def test_test_mode_existing_app_update_requirements(run_command, first_app):
    """Requirements can be updated for a test run."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["--test", "--update-requirements"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App will be built with a requirements update
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": False,
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": True, "passthrough": []},
        ),
    ]


def test_test_mode_existing_app_update_resources(run_command, first_app):
    """Resources can be updated in test mode."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["--test", "--update-resources"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App will be built with a resource update
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": False,
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": True, "passthrough": []},
        ),
    ]


def test_test_mode_update_existing_app(run_command, first_app):
    """An existing app can be updated and started in test mode."""
    # Add a single app
    run_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = run_command.parse_options(["-u", "--test"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App will be built; update is explicit
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": True,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Run the first app
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": True, "passthrough": []},
        ),
    ]


def test_test_mode_non_existent(run_command, first_app_config):
    """Requesting a test of a non-existent app causes a create."""
    # Add a single app, using the 'config only' fixture
    run_command.apps = {
        "first": first_app_config,
    }

    # Configure a test option
    options, _ = run_command.parse_options(["--test"])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App will be built in test mode, (which will transitively create)
        (
            "build",
            "first",
            {
                "test_mode": True,
                "update": False,
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "no_update": False,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Then, it will be started
        (
            "run",
            "first",
            {"build_state": "first", "test_mode": True, "passthrough": []},
        ),
    ]
