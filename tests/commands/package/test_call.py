def test_no_args_package_one_app(package_command, first_app):
    """If there is one app, package that app by default."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
    ]


def test_package_one_explicit_app(package_command, first_app, second_app):
    """If one app is named explicitly, package that app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line arguments
    options = package_command.parse_options([])

    # Run the build command on a specific app
    package_command(first_app, **options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
    ]


def test_no_args_package_two_app(package_command, first_app, second_app):
    """If there are multiple apps, publish all of them."""
    # Add two apps
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = package_command.parse_options([])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]


def test_no_sign_package_one_app(package_command, first_app):
    """If there is one app, and a --no-sign argument,package doesn't sign the
    app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure a no-sign option
    options = package_command.parse_options(["--no-sign"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": False,
            },
        ),
    ]


def test_identity_arg_package_one_app(package_command, first_app):
    """If there is one app,and an --identity argument, package signs the app
    with the specified identity."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an identity option
    options = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
            },
        ),
    ]


def test_adhoc_sign_package_one_app(package_command, first_app):
    """If there is one app,and an --adhoc argument, package signs the app using
    adhoc option."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an adhoc signing option
    options = package_command.parse_options(["--adhoc"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": True,
                "identity": None,
                "sign_app": True,
            },
        ),
    ]


def test_no_sign_args_package_two_app(package_command, first_app, second_app):
    """If there are multiple apps, and a --no-sign argument,package doesn't
    sign all the app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a no-sign option
    options = package_command.parse_options(["--no-sign"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": False,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]


def test_adhoc_sign_args_package_two_app(package_command, first_app, second_app):
    """If there are multiple apps,and an --adhoc argument, package signs all
    apps using adhoc option."""

    package_command.apps = {
        # Add the first app
        "first": first_app,
        # Add the second app
        "second": second_app,
    }

    # Configure adhoc command line options
    options = package_command.parse_options(["--adhoc"])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": True,
                "identity": None,
                "sign_app": True,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "packaging_format": "pkg",
                "adhoc_sign": True,
                "identity": None,
                "sign_app": True,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]


def test_identity_sign_args_package_two_app(package_command, first_app, second_app):
    """If there are multiple app,and an --identity argument, package signs all
    the apps with the specified identity."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure an identity option
    options = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]


def test_package_alternate_format(package_command, first_app):
    """An app can be packaged in an alternate format."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure command line options with an alternate format
    options = package_command.parse_options(["--packaging-format", "box"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "box",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
    ]


def test_create_before_package(package_command, first_app_config):
    """If the app hasn't been created, package creates the app first."""
    # Add a single app
    package_command.apps = {
        "first": first_app_config,
    }

    # Configure no command line options
    options = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # Create and then build the first app
        (
            "create",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "create_state": "first",
                "identity": None,
                "sign_app": True,
            },
        ),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "create_state": "first",
                "build_state": "first",
            },
        ),
    ]


def test_update_package_one_app(package_command, first_app):
    """If there is one app, and a -u argument, package updates the app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an update option
    options = package_command.parse_options(["-u"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # Update (and then build) the first app
        (
            "update",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "first",
            },
        ),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "first",
                "build_state": "first",
            },
        ),
    ]


def test_update_package_two_app(package_command, first_app, second_app):
    """If there are multiple apps, update and publish all of them."""
    # Add two apps
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure an update option
    options = package_command.parse_options(["--update"])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # Update (and then build) the first app
        (
            "update",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "first",
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "first",
                "build_state": "first",
            },
        ),
        # Update (and then build) the second app
        (
            "update",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                # state of previous calls have been preserved.
                "update_state": "first",
                "build_state": "first",
                "package_state": "first",
            },
        ),
        (
            "build",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "second",
                # state of previous calls have been preserved.
                "build_state": "first",
                "package_state": "first",
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "update_state": "second",
                "build_state": "second",
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]


def test_build_before_package(package_command, first_app_unbuilt):
    """If the an app hasn't been built, it is built before packaging."""
    # Add a single app
    package_command.apps = {
        "first": first_app_unbuilt,
    }

    # Configure no commmand line options
    options = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify",),
        # Build the first app
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
            },
        ),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "packaging_format": "pkg",
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "build_state": "first",
            },
        ),
    ]
