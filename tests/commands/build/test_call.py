import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_specific_app(build_command, first_app, second_app):
    """If a specific app is requested, build it."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options([])

    # Run the build command
    build_command(first_app, **options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Build the first app; no state
        ("build", "first", False, {}),
    ]


def test_multiple_apps(build_command, first_app, second_app):
    """If there are multiple apps, build all of them."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Build the first app; no state
        ("build", "first", False, {}),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Build the second apps; state from previous build.
        ("build", "second", False, {"build_state": "first"}),
    ]


def test_non_existent(build_command, first_app_config, second_app):
    """Requesting a build of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", False, {}),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"create_state": "first"}),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app *does* exist, so it only be built
        (
            "build",
            "second",
            False,
            {"create_state": "first", "build_state": "first"},
        ),
    ]


def test_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting a build of an app that has been created, but not build, just causes a
    build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # First App exists, but hasn't been built; it will be built.
        ("build", "first", False, {}),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app has been built before; it will be built again.
        ("build", "second", False, {"build_state": "first"}),
    ]


def test_update_app(build_command, first_app, second_app):
    """If an update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a -a command line option
    options, _ = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            False,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_update_app_requirements(build_command, first_app, second_app):
    """If a requirements update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options, _ = build_command.parse_options(["-r"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            False,
            {
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_update_app_support(build_command, first_app, second_app):
    """If a support update is requested, support is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options, _ = build_command.parse_options(["--update-support"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            False,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": True,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": True,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_update_app_stub(build_command, first_app, second_app):
    """If a stub update is requested, the stub is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options, _ = build_command.parse_options(["--update-stub"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            False,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": True,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": True,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_update_app_resources(build_command, first_app, second_app):
    """If a resources update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options, _ = build_command.parse_options(["--update-resources"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            False,
            {
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_update_non_existent(build_command, first_app_config, second_app):
    """Requesting an update of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", False, {}),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"create_state": "first"}),
        # Second app *does* exist, so it will be updated, then built
        (
            "update",
            "second",
            False,
            {
                "create_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {
                "create_state": "first",
                "build_state": "first",
                "update_state": "second",
            },
        ),
    ]


def test_update_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting an update of an unbuilt app causes an update before build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First App exists, but hasn't been built; it will be updated then built.
        (
            "update",
            "first",
            False,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", False, {"update_state": "first"}),
        # Second app has been built before; it will be built again.
        (
            "update",
            "second",
            False,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            False,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_test(build_command, first_app, second_app):
    """If the user builds a test app, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            True,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_test_no_update(build_command, first_app, second_app):
    """If the user builds a test app without app updates, requirements and resources are
    still updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test", "--no-update"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # No update of the first app
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {}),
        # No update of the second app
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"build_state": "first"},
        ),
    ]


def test_build_test_update_dependencies(build_command, first_app, second_app):
    """If the user builds a test app with app dependency updates, app code and resources
    are updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test", "-r"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            True,
            {
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": True,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_test_update_resources(build_command, first_app, second_app):
    """If the user builds a test app with app resource updates, app code and resources
    are updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test", "--update-resources"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            True,
            {
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": True,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_test_update_support(build_command, first_app, second_app):
    """If the user builds a test app with a support update, app code and support are
    updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test", "--update-support"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            True,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": True,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": True,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_test_update_stub(build_command, first_app, second_app):
    """If the user builds a test app with stub update, app code and stub are updated
    before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--test", "--update-stub"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update then build the first app
        (
            "update",
            "first",
            True,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": True,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"update_state": "first"}),
        # Update then build the second app
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": True,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


def test_build_invalid_update(build_command, first_app, second_app):
    """If the user requests a build with update and no-update, an error is raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["-u", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_requirements(build_command, first_app, second_app):
    """If the user requests a build with update-requirements and no-update, an error is
    raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["-r", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-requirements and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_resources(build_command, first_app, second_app):
    """If the user requests a build with update-resources and no-update, an error is
    raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--update-resources", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-resources and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_support(build_command, first_app, second_app):
    """If the user requests a build with update-support and no-update, an error is
    raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--update-support", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-support and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_stub(build_command, first_app, second_app):
    """If the user requests a build with update-stub and no-update, an error is
    raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--update-stub", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-stub and --no-update",
    ):
        build_command(**options)


def test_test_app_non_existent(build_command, first_app_config, second_app):
    """Requesting a test build of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["-u", "--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", True, {}),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", True, {"create_state": "first"}),
        # Second app *does* exist, so it will be updated, then built
        (
            "update",
            "second",
            True,
            {
                "create_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {
                "create_state": "first",
                "build_state": "first",
                "update_state": "second",
            },
        ),
    ]


def test_test_app_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting a test build with update of an unbuilt app causes an update before
    build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["-u", "--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First App exists, but hasn't been built; it will be updated then built.
        (
            "update",
            "first",
            True,
            {
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        (
            "build",
            "first",
            True,
            {"update_state": "first"},
        ),
        # Second app has been built before; it will be built again.
        (
            "update",
            "second",
            True,
            {
                "update_state": "first",
                "build_state": "first",
                "update_requirements": False,
                "update_resources": False,
                "update_support": False,
                "update_stub": False,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            True,
            {"update_state": "second", "build_state": "first"},
        ),
    ]


# Parametrize both --apps/-a flags
@pytest.mark.parametrize("app_flags", ["--app", "-a"])
def test_build_app_single(build_command, first_app, second_app, app_flags):
    """If the --app or -a flag is used, only the selected app is built."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options with the parameterized flag
    options, _ = build_command.parse_options([app_flags, "first"])

    # Run the build command
    build_command(**options)

    # Only the selected app is built
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Build the first app
        ("build", "first", False, {}),
    ]


def test_build_app_invalid(build_command, first_app, second_app):
    """If an invalid app name is passed to --app, an error is raised."""
    # Add two valid apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options, _ = build_command.parse_options(["--app", "invalid"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        build_command(**options)


def test_build_app_none_defined(build_command):
    """If no apps are defined, do nothing."""
    # No apps available
    build_command.apps = {}

    # Configure command line options
    options, _ = build_command.parse_options([])

    # Run the build command
    result = build_command(**options)

    # Nothing is built
    assert result is None
    assert build_command.actions == [("verify-host",), ("verify-tools",)]


def test_build_app_all_flags(build_command, first_app, second_app):
    """Verify that all build-related update flags work correctly with -a."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line with all available flags
    options, _ = build_command.parse_options(
        [
            "-a",
            "first",
            "--test",
            "--update",
            "--update-requirements",
            "--update-resources",
            "--update-support",
            "--update-stub",
        ]
    )

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First app is updated with all update flags
        (
            "update",
            "first",
            True,
            {
                "update_requirements": True,
                "update_resources": True,
                "update_support": True,
                "update_stub": True,
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # First app is built in test mode
        ("build", "first", True, {"update_state": "first"}),
    ]
